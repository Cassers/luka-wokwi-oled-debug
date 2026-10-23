#!/usr/bin/env python3
"""Puente TCP <-> Wokwi RFC2217 para el depurador GHI (Windows, macOS o Linux).

Alternativa sin drivers al puente PTY de Linux (wokwi_debug_bridge.py).
Wokwi expone el UART0 simulado por RFC2217 (puerto 4000). Este puente abre
un servidor TCP local (127.0.0.1:4001) que entrega los mismos bytes, ya sin la
negociación Telnet. GHI se conecta con debugPort = "tcp://127.0.0.1:4001",
lo que requiere el parche TCP de tools/parchar_ghi.py.

Uso (lo lanzan las tareas de VS Code):
  python tools/wokwi_debug_bridge_tcp.py --ensure   # inicia o reutiliza
  python tools/wokwi_debug_bridge_tcp.py --check    # ¿hay un puente vivo?

Un solo cliente a la vez. GHI cierra y reabre la conexión al reiniciar el
dispositivo: el puente sigue vivo y acepta la nueva conexión. Lo que llega de
Wokwi sin cliente conectado se guarda (hasta 64 KB), como haría un puerto serie.
No se inyectan comandos ni pulsos de reinicio; DTR/RTS quedan desactivados.
Si Wokwi se detiene, el puente termina: vuelve a lanzar el perfil.
Solo escucha en 127.0.0.1.
"""

import argparse
import json
import socket
import sys
import threading
import time

HOST = "127.0.0.1"
MAX_PENDING = 65536
STATUS_VERSION = 1


def status_record(args):
    return {"version": STATUS_VERSION, "bridge": "wokwi-ghi-tcp",
            "rfc2217": args.port, "tcp": args.tcp_port, "baud": args.baud}


def query_status(control_port, timeout=1.0):
    """Pregunta al puente vivo por su configuración; None si no hay puente."""
    try:
        with socket.create_connection((HOST, control_port), timeout=timeout) as s:
            data = b""
            while not data.endswith(b"\n") and len(data) < 4096:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
        record = json.loads(data.decode("utf-8"))
        return record if record.get("bridge") == "wokwi-ghi-tcp" else None
    except (OSError, ValueError):
        return None


def bridge(args):
    import serial

    stop = threading.Event()
    lock = threading.Lock()
    pending = bytearray()      # Wokwi -> cliente, mientras no hay cliente
    state = {"client": None, "error": None}

    remote = serial.serial_for_url(
        f"rfc2217://{HOST}:{args.port}", baudrate=args.baud, timeout=0.1,
        do_not_open=True,
    )
    remote.dtr = False
    remote.rts = False
    remote.open()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for s in (server, control):
        if sys.platform == "win32":
            s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    server.bind((HOST, args.tcp_port))
    control.bind((HOST, args.control_port))
    server.listen(1)
    control.listen(4)
    server.settimeout(0.2)
    control.settimeout(0.2)

    def fail(exc):
        if state["error"] is None:
            state["error"] = exc
        stop.set()

    def send_to_client(data):
        with lock:
            client = state["client"]
            if client is None:
                pending.extend(data)
                del pending[:-MAX_PENDING]
                return
        try:
            client.sendall(data)
        except OSError:
            drop_client(client)
            with lock:
                pending.extend(data)
                del pending[:-MAX_PENDING]

    def drop_client(client):
        with lock:
            if state["client"] is client:
                state["client"] = None
        try:
            client.close()
        except OSError:
            pass

    def from_wokwi():
        try:
            while not stop.is_set():
                data = remote.read(max(1, min(remote.in_waiting, 4096)))
                if data:
                    send_to_client(data)
        except (OSError, serial.SerialException) as exc:
            fail(exc)

    def from_client(client):
        try:
            while not stop.is_set():
                try:
                    data = client.recv(4096)
                except socket.timeout:
                    continue
                if not data:
                    break
                remote.write(data)
        except serial.SerialException as exc:
            fail(exc)               # Wokwi se fue: el puente termina
        except OSError:
            pass                    # GHI cerró la conexión: esperar otra
        finally:
            drop_client(client)

    def serve_control():
        line = (json.dumps(status_record(args)) + "\n").encode("utf-8")
        while not stop.is_set():
            try:
                conn, _ = control.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                conn.sendall(line)
            except OSError:
                pass
            finally:
                conn.close()

    threads = [threading.Thread(target=from_wokwi, daemon=True),
               threading.Thread(target=serve_control, daemon=True)]
    for t in threads:
        t.start()

    print(f"GHI debugPort: tcp://{HOST}:{args.tcp_port}", flush=True)
    print(f"RFC2217: {HOST}:{args.port}; {args.baud} baud; control {HOST}:{args.control_port}",
          flush=True)
    print("Puente activo. Ctrl+C para cerrar; no ejecutar mpremote en paralelo.", flush=True)
    try:
        while not stop.is_set():
            try:
                client, _ = server.accept()
            except socket.timeout:
                continue
            with lock:
                busy = state["client"] is not None
            if busy:
                client.close()      # un solo cliente: GHI
                continue
            client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            client.settimeout(0.2)
            with lock:
                backlog = bytes(pending)
                pending.clear()
                state["client"] = client
            if backlog:
                try:
                    client.sendall(backlog)
                except OSError:
                    drop_client(client)
                    continue
            print("GHI conectado.", flush=True)
            threading.Thread(target=from_client, args=(client,), daemon=True).start()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        with lock:
            client = state["client"]
            state["client"] = None
        for s in (client, server, control):
            if s is not None:
                try:
                    s.close()
                except OSError:
                    pass
        remote.close()
    if state["error"] is not None:
        raise RuntimeError(f"RFC2217 desconectado: {state['error']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=4000, help="RFC2217 de Wokwi")
    parser.add_argument("--tcp-port", type=int, default=4001, help="puerto para GHI")
    parser.add_argument("--control-port", type=int, default=4002, help="puerto de estado")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--check", action="store_true", help="solo comprueba el puente vivo")
    parser.add_argument("--ensure", action="store_true", help="reutiliza un puente vivo o inicia uno")
    args = parser.parse_args()
    ports = (args.port, args.tcp_port, args.control_port)
    if any(not 1 <= p <= 65535 for p in ports) or len(set(ports)) != 3 or args.baud <= 0:
        parser.error("Puertos o baud inválidos")

    record = query_status(args.control_port)
    if args.check:
        if record is None:
            print("Puente NO listo: no responde en "
                  f"{HOST}:{args.control_port}. Inicia la simulación y relanza el perfil.",
                  file=sys.stderr)
            return 1
        if record != status_record(args):
            print(f"Puente NO listo: vivo con otra configuración {record}", file=sys.stderr)
            return 1
        print(f"Puente listo: tcp://{HOST}:{args.tcp_port} -> RFC2217 {args.port}")
        return 0
    if record is not None:
        if args.ensure and record == status_record(args):
            print("Puente activo. Reutilizando el puente que ya corre.", flush=True)
            return 0
        print(f"Puente no disponible: ya hay otro puente con {record}", file=sys.stderr)
        return 1
    print("Iniciando puente RFC2217 (TCP)...", flush=True)
    try:
        bridge(args)
    except (OSError, RuntimeError) as exc:
        print(f"Puente no disponible: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
