# Depurar MicroPython en Wokwi y ver la OLED

Demo de diagnóstico para Luka: pausar MicroPython dentro de un ESP32 **simulado** en Wokwi (VS Code + GHI MicroPython Debugger) y comprobar a la vez variables, pila de llamadas y pantalla OLED SSD1306.

**Guía web (tutorial de uso, pines y ruta de práctica):** https://cassers.github.io/luka-wokwi-oled-debug/
Instalación inicial (para la IA tutora): [MicroPython-debug/GUIA-BOT-LUKA.md](MicroPython-debug/GUIA-BOT-LUKA.md).

## Obtener los archivos

```sh
git clone https://github.com/Cassers/luka-wokwi-oled-debug.git
cd luka-wokwi-oled-debug
code .
```

Sin git: botón **Code → Download ZIP** y abrir en VS Code la carpeta descomprimida (la raíz, no solo `MicroPython-debug/`).

## Qué contiene

```text
.vscode/launch.json   perfiles de depuración remota GHI
.vscode/tasks.json    tareas que arrancan y comprueban el puente
tools/wokwi_debug_bridge.py   puente RFC2217 → PTY (Linux)
MicroPython-debug/    demo OLED, practica.py (ejercicios), controlador ssd1306, circuito Wokwi y guía
chips/                4 circuitos extra: DHT22, MPU6050 (I2C), MAX7219 (SPI), UART
sensores/             6 sensores por tipo de señal: botón, PIR, potenciómetro, LDR, HC-SR04, DS18B20
index.html            la guía web (GitHub Pages)
```

## Practicar

Después de la demo, la guía web tiene una **ruta de práctica** (teoría → práctica → concepto nuevo → práctica…). Se trabaja en `MicroPython-debug/practica.py` con el perfil **Práctica OLED — REMOTA GHI**.

## Hablar con otros chips

Cada carpeta de `chips/` trae su programa, `diagram.json`, `wokwi.toml` y perfil de depuración (**Chip N · … — REMOTA GHI**). En Wokwi: Select Config File → `chips/<carpeta>/wokwi.toml`. Explicación paso a paso en la guía web, sección «Hablar con otros chips».

## Laboratorio de sensores

Cada carpeta de `sensores/` trae su programa, `diagram.json`, `wokwi.toml` y perfil (**Sensor N · … — REMOTA GHI**). En Wokwi: Select Config File → `sensores/<carpeta>/wokwi.toml`. Explicación en la guía web, sección «Laboratorio de sensores».

## Qué NO contiene (lo preparas tú siguiendo la guía)

- `.venv/` — se crea en el paso 3 (`pyserial==3.5`).
- `.tools/ghi-debug/` — firmware GHI que se descarga y verifica en el paso 5.
- El parche de la extensión GHI 0.2.2 — se aplica en tu instalación de VS Code en el paso 6.

Las menciones a la carpeta `MicroPython/` en el README de la demo se refieren al ejemplo normal del profesor (fallback opcional), que no forma parte de este repositorio.

## Alcance

Probado en Linux x86_64, VS Code 1.140, GHI MicroPython Debugger 0.2.2 y pyserial 3.5. La combinación GHI + Wokwi es experimental y usa un ajuste local; no es soporte oficial de GHI. Todo se ejecuta en simulación: **no flashear hardware físico**.
