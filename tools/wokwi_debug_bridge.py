#!/usr/bin/env python3
"""Experimental Linux PTY <-> Wokwi RFC2217 bridge for GHI's UART adapter.

Run from the repository: .venv/bin/python tools/wokwi_debug_bridge.py
For a VS Code background task: add --ensure --recover-stale. Validate readiness
in a dependent task with --check. Never use Debug Anyway after a failed check.
Use the printed .tools/wokwi-ghi-uart path as GHI's debugPort, with
debugInterface="uart" and debugBaud=115200. Only loopback TCP is accepted.

pyserial handles Telnet negotiation and escaping, including binary 0xff.
No MicroPython/GHI commands or reset pulses are injected. DTR/RTS start
deasserted; PTY modem-line changes are not forwarded. The slave is held open
so GHI may close/reopen it around its own protocol reboot. Stop/start of the
Wokwi simulator requires restarting this bridge. Do not share port 4000 with
mpremote while the bridge is running. This does not prove GHI/Wokwi support.

Transport evidence (reviewed commit):
https://github.com/ghi-electronics/micropython-vsc-extension/blob/
3a9dc1dc9f4c7deff29894bb816a39e1cabba2fa/src/deviceLink.ts
The UART launch/reopen flow is in src/debugSession.ts, launchUart().
"""

import argparse
import json
import os
from pathlib import Path
import pty
import queue
import select
import signal
import stat
import sys
import tempfile
import threading
import tty


def identity(info):
    return [info.st_dev, info.st_ino, info.st_rdev]


def process_start(pid):
    # /proc/PID/stat field 22; comm may itself contain spaces/parentheses.
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()
    if fields[0] == "Z":
        raise RuntimeError("El proceso del puente terminó")
    return fields[19]


def metadata_path(link):
    return link.with_name(link.name + ".json")


def publish_metadata(link, master, slave, host, port, baud):
    """Publish a complete ownership record atomically, without replacing files."""
    record = {
        "version": 1, "pid": os.getpid(),
        "starttime": process_start(os.getpid()),
        "script": str(Path(__file__).resolve()),
        "link": str(link), "link_identity": identity(link.lstat()),
        "slave": os.ttyname(slave), "slave_identity": identity(os.fstat(slave)),
        "master_fd": master, "slave_fd": slave,
        "host": host, "port": port, "baud": baud,
    }
    destination = metadata_path(link)
    fd, temporary = tempfile.mkstemp(prefix=".wokwi-bridge-", dir=link.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(record, stream)
            stream.flush()
            os.fsync(stream.fileno())
            own_identity = identity(os.fstat(stream.fileno()))
        # link() is atomic and refuses any existing destination, including symlinks.
        os.link(temporary, destination)
        return own_identity
    finally:
        os.unlink(temporary)


def check_runtime(link):
    """Read metadata and /proc only; never open the PTY or a network socket."""
    metadata = metadata_path(link)
    info = metadata.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
        raise RuntimeError("Metadatos no regulares o de otro usuario")
    record = json.loads(metadata.read_text())
    script = Path(__file__).resolve()
    if record["version"] != 1 or record["script"] != str(script):
        raise RuntimeError("Metadatos de otro script o versión")
    pid = record["pid"]
    if type(pid) is not int or pid <= 0:
        raise RuntimeError("PID inválido")
    if process_start(pid) != record["starttime"]:
        raise RuntimeError("PID reciclado: starttime no coincide")
    proc = Path(f"/proc/{pid}")
    argv = (proc / "cmdline").read_bytes().rstrip(b"\0").split(b"\0")
    # Accept our direct Python invocation, with simple flags such as -B/-u.
    arguments = [os.fsdecode(a) for a in argv[1:]]
    while arguments and arguments[0] in ("-B", "-u", "-E", "-s", "-S", "-I", "-O", "-OO"):
        arguments.pop(0)
    if not arguments or "--check" in arguments[1:]:
        raise RuntimeError("El PID no ejecuta el puente")
    invoked = Path(arguments[0])
    if not invoked.is_absolute():
        invoked = (proc / "cwd").resolve() / invoked
    if invoked.resolve() != script:
        raise RuntimeError("El PID ejecuta un comando diferente")
    if record["link"] != str(link) or not link.is_symlink():
        raise RuntimeError("Enlace del puente inválido")
    if identity(link.lstat()) != record["link_identity"]:
        raise RuntimeError("El enlace fue reemplazado")
    slave_path = Path(record["slave"])
    if slave_path.parent != Path("/dev/pts") or not slave_path.name.isdecimal():
        raise RuntimeError("Destino PTY inválido")
    if os.readlink(link) != str(slave_path):
        raise RuntimeError("El destino del enlace cambió")
    slave_info = slave_path.stat()
    if not stat.S_ISCHR(slave_info.st_mode) or identity(slave_info) != record["slave_identity"]:
        raise RuntimeError("PTY reemplazado o reciclado")
    for key in ("master_fd", "slave_fd"):
        if type(record[key]) is not int or record[key] < 0:
            raise RuntimeError("Descriptor inválido")
    if identity((proc / "fd" / str(record["slave_fd"])).stat()) != record["slave_identity"]:
        raise RuntimeError("El proceso ya no mantiene el PTY slave")
    fdinfo = (proc / "fdinfo" / str(record["master_fd"])).read_text()
    tty_index = next((s.split(":", 1)[1].strip() for s in fdinfo.splitlines()
                      if s.startswith("tty-index:")), None)
    if tty_index != slave_path.name:
        raise RuntimeError("El master del proceso no corresponde al PTY")
    if process_start(pid) != record["starttime"]:
        raise RuntimeError("El proceso cambió durante la comprobación")
    return pid


def recover_stale(link):
    """Remove only recorded artifacts of a dead PID; never open their target."""
    metadata = metadata_path(link)
    info = metadata.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
        raise RuntimeError("No se recuperan metadatos ajenos o no regulares")
    contents = metadata.read_text()
    record = json.loads(contents)
    if (record["version"] != 1
            or record["script"] != str(Path(__file__).resolve())
            or record["link"] != str(link)
            or not isinstance(record["starttime"], str)
            or not record["starttime"].isdecimal()):
        raise RuntimeError("No se recuperan metadatos de origen diferente")
    pid = record["pid"]
    if type(pid) is not int or pid <= 0:
        raise RuntimeError("No se recupera un PID inválido")
    proc = Path(f"/proc/{pid}")
    if os.path.lexists(proc):
        raise RuntimeError("PID aún existente (incluso reciclado): no se retira nada")
    link_info = link.lstat()
    if (not stat.S_ISLNK(link_info.st_mode) or link_info.st_uid != os.getuid()
            or identity(link_info) != record["link_identity"]
            or os.readlink(link) != record["slave"]):
        raise RuntimeError("Enlace ajeno o reemplazado: no se retira nada")
    # Recheck immediately before unlinking, without stat/open on /dev/pts/N.
    if (os.path.lexists(proc) or identity(link.lstat()) != record["link_identity"]
            or identity(metadata.lstat()) != identity(info)
            or metadata.read_text() != contents):
        raise RuntimeError("Los restos cambiaron durante la comprobación")
    link.unlink()
    metadata.unlink()
    print("Restos propios de puente terminado retirados: enlace y metadatos; PTY intacto.",
          flush=True)


def bridge(host, port, baud, link):
    """Relay bytes until interrupted or the RFC2217 connection fails."""
    import serial

    stop = threading.Event()
    incoming = queue.Queue(maxsize=64)
    errors = []
    master = slave = None
    reader = None
    link_identity = None
    metadata_identity = None
    remote = serial.serial_for_url(
        f"rfc2217://{host}:{port}", baudrate=baud, timeout=0.1,
        do_not_open=True,
    )
    # pyserial applies these states during negotiation; never pulse EN/BOOT.
    remote.dtr = False
    remote.rts = False

    def receive():
        try:
            while not stop.is_set():
                data = remote.read(max(1, min(remote.in_waiting, 4096)))
                if data:
                    while not stop.is_set():
                        try:
                            incoming.put(data, timeout=0.1)
                            break
                        except queue.Full:
                            pass
        except (OSError, serial.SerialException) as exc:
            errors.append(exc)
            stop.set()

    previous_handlers = {}
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[sig] = signal.signal(sig, lambda *_: stop.set())
        remote.open()
        master, slave = pty.openpty()
        tty.setraw(slave)
        os.set_blocking(master, False)
        # Exclusive creation: never overwrite an existing file or symlink.
        link.symlink_to(os.ttyname(slave))
        info = link.lstat()
        link_identity = (info.st_dev, info.st_ino)
        reader = threading.Thread(target=receive, daemon=True)
        reader.start()
        metadata_identity = publish_metadata(link, master, slave, host, port, baud)
        print(f"GHI debugPort: {link}", flush=True)
        print(f"PTY: {os.ttyname(slave)}; RFC2217: {host}:{port}; {baud} baud",
              flush=True)
        print("Puente activo. Ctrl+C para cerrar; no ejecutar mpremote en paralelo.",
              flush=True)
        pending = bytearray()
        while not stop.is_set():
            while len(pending) < 65536:
                try:
                    pending.extend(incoming.get_nowait())
                except queue.Empty:
                    break
            readable, writable, _ = select.select(
                [master], [master] if pending else [], [], 0.05,
            )
            if master in readable:
                try:
                    data = os.read(master, 4096)
                except BlockingIOError:
                    data = b""
                if data:
                    remote.write(data)
            if master in writable:
                try:
                    sent = os.write(master, pending)
                    del pending[:sent]
                except BlockingIOError:
                    pass
        if errors:
            raise RuntimeError(f"RFC2217 desconectado: {errors[0]}")
    finally:
        stop.set()
        remote.close()
        if reader is not None:
            reader.join(timeout=1)
        if metadata_identity is not None:
            try:
                if identity(metadata_path(link).lstat()) == metadata_identity:
                    metadata_path(link).unlink()
            except FileNotFoundError:
                pass
        if link_identity is not None:
            try:
                info = link.lstat()
                if (info.st_dev, info.st_ino) == link_identity:
                    link.unlink()
            except FileNotFoundError:
                pass
        for fd in (master, slave):
            if fd is not None:
                os.close(fd)
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("localhost", "127.0.0.1"),
                        default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4000)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--check", action="store_true",
                        help="Valida dueño del PTY sin abrir puertos ni conectar")
    parser.add_argument("--ensure", action="store_true",
                        help="Reutiliza un puente validado o ejecuta uno nuevo en primer plano")
    parser.add_argument("--recover-stale", action="store_true",
                        help="Retira solo enlace/metadatos propios de un PID ya inexistente")
    parser.add_argument("--link", type=Path,
                        help="Enlace PTY dentro de .tools/ (por defecto wokwi-ghi-uart)")
    args = parser.parse_args()
    if args.check and (args.ensure or args.recover_stale):
        parser.error("--check no se combina con --ensure ni --recover-stale")
    if not 1 <= args.port <= 65535 or args.baud <= 0:
        parser.error("Puerto o baud inválido")
    workspace = Path(__file__).resolve().parent.parent
    tools = workspace / ".tools"
    if not args.check:
        tools.mkdir(exist_ok=True)
    if tools.resolve() != tools:
        parser.error(".tools debe ser un directorio local, no un enlace")
    link = args.link or tools / "wokwi-ghi-uart"
    link = Path(os.path.abspath(link))
    if not link.parent.resolve().is_relative_to(tools) or link == tools:
        parser.error("--link debe estar dentro de .tools/")
    if args.check:
        try:
            pid = check_runtime(link)
        except (OSError, RuntimeError, ValueError, KeyError, TypeError, IndexError) as exc:
            print(f"Puente NO listo: {exc}. Reinicia el puente; no abras el PTY.",
                  file=sys.stderr)
            return 1
        print(f"Puente listo: PID {pid}, PTY y propietario verificados ({link})")
        return 0
    try:
        exists = os.path.lexists(link) or os.path.lexists(metadata_path(link))
        if exists and args.ensure:
            try:
                pid = check_runtime(link)
            except (OSError, RuntimeError, ValueError, KeyError, TypeError, IndexError):
                if not args.recover_stale:
                    raise RuntimeError("Puente existente no válido; no se reutiliza")
            else:
                record = json.loads(metadata_path(link).read_text())
                if (record.get("host"), record.get("port"), record.get("baud")) != (args.host, args.port, args.baud):
                    raise RuntimeError("Puente vivo con otro endpoint/baud; reinícialo explícitamente")
                print(f"Puente activo. Reutilizando PID {pid}, propiedad verificada.", flush=True)
                return 0
        if exists:
            if not args.recover_stale:
                raise RuntimeError(f"Ya existe {link}; no se sobrescribe")
            recover_stale(link)
        print("Iniciando puente RFC2217...", flush=True)
        bridge(args.host, args.port, args.baud, link)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, IndexError) as exc:
        print(f"Puente no disponible: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
