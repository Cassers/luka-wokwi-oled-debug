#!/usr/bin/env python3
"""Aplica los dos ajustes locales a GHI MicroPython Debugger 0.2.2 (Windows, macOS, Linux).

1. debugSession.js: reintenta 3 veces el «attach» tras el reinicio (Wokwi tarda
   en arrancar). Es el mismo bloque del Paso 6 de GUIA-BOT-LUKA.md.
2. deviceLink.js: acepta debugPort = "tcp://127.0.0.1:4001" además de un
   puerto serie. Así GHI habla con tools/wokwi_debug_bridge_tcp.py sin drivers.

Uso, desde la raíz del repositorio y con VS Code sin depurar:
  python tools/parchar_ghi.py           # aplica (idempotente)
  python tools/parchar_ghi.py --check   # solo informa
Después: VS Code → «Developer: Reload Window».

Guarda copias originales en .tools/ghi-debug/ (nunca las sobrescribe).
Si la extensión no coincide exactamente con 0.2.2, no toca nada.
"""

import argparse
import os
from pathlib import Path
import shutil
import sys

EXTENSION = "ghielectronics.micropython-debugger-0.2.2"
MARK_RETRY = "UART still booting; retrying attachment"
MARK_TCP = "METIS-TCP-PATCH"

RETRY_ANCHOR = """        this.log(`Reopening UART on ${port}...`);
        await this.link.open(port, baud);
        this.attachEvents();
        await this.link.conditions(4 /* Cond.Attached */, 0);
"""
RETRY_NEW = """        this.log(`Reopening UART on ${port}...`);
        await this.link.open(port, baud);
        this.attachEvents();
        // Wokwi can finish booting after UART has already been reopened.
        // A frame sent too early is lost; retry attachment within a bounded window.
        let uartAttached = false;
        for (let attempt = 1; attempt <= 3; attempt++) {
            try {
                await this.link.conditions(4 /* Cond.Attached */, 0);
                uartAttached = true;
                break;
            }
            catch (err) {
                if (attempt === 3) {
                    throw err;
                }
                this.log(`UART still booting; retrying attachment (${attempt}/3)...`);
                await delay(250);
            }
        }
        if (!uartAttached) {
            throw new Error("UART did not become ready after reboot");
        }
"""

TCP_ANCHOR = """    async open(path, baudRate = 115200) {
        await new Promise((resolve, reject) => {
"""
TCP_NEW = """    async open(path, baudRate = 115200) {
        await new Promise((resolve, reject) => {
            // METIS-TCP-PATCH: debugPort "tcp://host:port" -> plain TCP socket
            // (Wokwi RFC2217 bridge, tools/wokwi_debug_bridge_tcp.py).
            if (/^tcp:\\/\\//i.test(path)) {
                const net = require("net");
                const target = new URL(path);
                const sock = net.connect({ host: target.hostname, port: Number(target.port) });
                const port = new events_1.EventEmitter();
                port.isOpen = false;
                port.write = (data, cb) => sock.write(data, cb);
                port.drain = (cb) => {
                    if (sock.writableNeedDrain) {
                        sock.once("drain", () => cb && cb());
                    }
                    else {
                        setImmediate(() => cb && cb());
                    }
                };
                port.close = (cb) => {
                    port.isOpen = false;
                    if (sock.destroyed) {
                        setImmediate(() => cb && cb());
                        return;
                    }
                    sock.once("close", () => cb && cb());
                    sock.end();
                    setTimeout(() => sock.destroy(), 300);
                };
                sock.setNoDelay(true);
                sock.on("data", (d) => this.onData(d));
                sock.on("error", (e) => {
                    if (!port.isOpen) {
                        reject(new Error(`Cannot connect to ${path}: ${e.message}. Is the Wokwi bridge task running?`));
                    }
                    else {
                        this.emit("error", e);
                    }
                });
                sock.on("close", () => {
                    if (port.isOpen) {
                        port.isOpen = false;
                        this.emit("close");
                    }
                });
                sock.once("connect", () => {
                    port.isOpen = true;
                    this.port = port;
                    resolve();
                });
                return;
            }
"""

PATCHES = [
    ("debugSession.js", MARK_RETRY, RETRY_ANCHOR, RETRY_NEW),
    ("deviceLink.js", MARK_TCP, TCP_ANCHOR, TCP_NEW),
]


def candidates():
    home = Path.home()
    roots = [home / ".vscode" / "extensions", home / ".vscode-insiders" / "extensions"]
    if os.environ.get("VSCODE_EXTENSIONS"):
        roots.insert(0, Path(os.environ["VSCODE_EXTENSIONS"]))
    return [r / EXTENSION / "out" for r in roots if (r / EXTENSION / "out").is_dir()]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="solo informa, no cambia nada")
    parser.add_argument("--out", type=Path, help="carpeta out/ de la extensión (si no se encuentra sola)")
    args = parser.parse_args()

    outs = [args.out] if args.out else candidates()
    if not outs:
        print(f"No encontré {EXTENSION}. Instala GHI MicroPython Debugger 0.2.2 "
              "o pasa --out <carpeta out de la extensión>.", file=sys.stderr)
        return 1
    backups = Path(__file__).resolve().parent.parent / ".tools" / "ghi-debug"
    status = 0
    for out in outs:
        print(f"Extensión: {out}")
        for name, mark, anchor, new in PATCHES:
            path = out / name
            with open(path, encoding="utf-8", newline="") as f:
                text = f.read()
            if mark in text:
                print(f"  {name}: ya ajustado")
                continue
            if text.replace("\r\n", "\n").count(anchor) != 1:
                print(f"  {name}: versión distinta, no se toca (busca el bloque a mano)",
                      file=sys.stderr)
                status = 1
                continue
            if args.check:
                print(f"  {name}: FALTA el ajuste")
                status = 1
                continue
            backups.mkdir(parents=True, exist_ok=True)
            backup = backups / name.replace(".js", ".original.js")
            if not backup.exists():
                shutil.copy2(path, backup)
                print(f"  copia original: {backup}")
            crlf = "\r\n" in text
            patched = text.replace(anchor.replace("\n", "\r\n"), new.replace("\n", "\r\n")) if crlf else text.replace(anchor, new)
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(patched)
            print(f"  {name}: ajuste aplicado")
    if not args.check and status == 0:
        print("Listo. En VS Code: Ctrl+Shift+P → «Developer: Reload Window».")
    return status


if __name__ == "__main__":
    sys.exit(main())
