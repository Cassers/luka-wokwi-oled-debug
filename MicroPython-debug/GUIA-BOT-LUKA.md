# Guía para la IA de Luka: depurar MicroPython y ver la OLED en Wokwi

## Propósito y evidencia

Reproducir la demo de diagnóstico de Sergio: detener Python remoto y observar contador, pila y pantalla juntos.
Sergio confirmó capturas del éxito el **16 de octubre de 2026**: `oled_demo.py:29`, contador 1 y OLED «vuelta 1».
Equipo probado: **Linux x86_64, VS Code 1.140, GHI MicroPython Debugger 0.2.2 y pyserial 3.5**.
La combinación GHI + Wokwi es experimental y requiere un parche local; no garantiza otros SO o versiones.
El comentario histórico de `oled_demo.py` que dice «aún no confirmada» precede al éxito registrado en el README.

## Contrato del bot tutor

- Explica en español, da **un solo paso**, pide el resultado y espera antes del siguiente.
- Ante un fallo, pide el mensaje completo y confirma el contexto; cambia una cosa por vez.
- Enseña con preguntas y pistas. No resuelvas ejercicios o exámenes ni escribas lógica de robots sin permiso docente explícito.
- Esta demo es diagnóstico del entorno de Sergio; no autoriza resolver el trabajo de Luka.
- Para APIs nuevas, verificar Context7 `/micropython/micropython`; si no está disponible, declarar la limitación. No afirmar verificación inexistente.
- No flashear hardware físico, tocar puertos USB ni instalar `machine` con pip: el código se ejecuta en MicroPython simulado.

## Paso 1 · Inventariar antes de instalar

Pregunta SO, arquitectura, versión de VS Code, shell, carpeta abierta y perfil activo de extensiones.
Confirma si dispone de Python para el puente, extensión Wokwi y permiso para ejecutar tareas del proyecto.
El puente actual usa PTY Linux y `/proc`; Windows/macOS requieren adaptación, no basta cambiar una ruta.
Si el equipo no es Linux, documentar esa diferencia y acordar adaptación antes de presentar este procedimiento como reproducible.
**Pide confirmación:** «¿Qué sistema y versión tienes, y qué carpeta está abierta?».

## Paso 2 · Transferir los archivos y abrir la raíz

Conserva esta estructura relativa en la copia del estudiante:

```text
raíz-del-proyecto/
├── .vscode/
│   ├── launch.json
│   └── tasks.json
├── tools/wokwi_debug_bridge.py
└── MicroPython-debug/
    ├── main.py
    ├── oled_demo.py
    ├── ssd1306.py
    ├── diagram.json
    ├── wokwi.toml
    └── README.md
```

Abre **la raíz** en VS Code, no únicamente `MicroPython-debug/`: las tareas y perfiles usan `${workspaceFolder}`.
No copies `.venv` del profesor; recréalo en el equipo destino. No supongas que `.tools/` viene de Git.
`MicroPython/` es opcional como fallback normal; sus perfiles adicionales no son necesarios para esta demo.
Si la copia ya tiene configuraciones propias, revisa su integración sin sobrescribirlas a ciegas.
**Pide confirmación:** presencia de archivos y carpeta raíz abierta.

## Paso 3 · Preparar Python del puente en Linux

Los comandos siguientes son para Linux, desde la raíz, una vez confirmado que `python3` existe.
Si `.venv` ya existe, inspecciónalo primero; usa el entorno correcto, sin recrearlo ni instalar globalmente a ciegas.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install pyserial==3.5
.venv/bin/python -m pip show pyserial
```

Las dos tareas invocan `${workspaceFolder}/.venv/bin/python`; confirma que esa ruta existe en el equipo destino.
Python del PC ejecuta el puente; el programa OLED se ejecutará en el ESP32 virtual.
**Pide confirmación:** entorno utilizable y pyserial 3.5 reconocido.

## Paso 4 · Instalar el adaptador correcto en la ventana correcta

En Extensiones de esa misma ventana/perfil, busca `@id:ghielectronics.micropython-debugger`.
Comprueba también que la extensión Wokwi (`Wokwi.wokwi-vscode`) esté disponible y pueda iniciar una simulación; resuelve cualquier activación pendiente con la cuenta del estudiante.
Para reproducir la prueba, instala **0.2.2**; comprueba nombre, identificador, versión y estado habilitado.
Ver **Disable/Uninstall** en la ficha evidencia instalación; comprueba además que no esté deshabilitada para este workspace.
El manifest instalado declara `engines.vscode: ^1.85.0`; la prueba real fue en 1.140, no en todas las versiones compatibles.
El perfil usará `type: micropython`. No elegir debugpy, «Python Debugger» ni C++ para este flujo.
Instalar GHI en otra ventana o perfil no acredita que esté disponible aquí.
**Pide confirmación:** identificador, versión y estado de la extensión en la ventana de trabajo.

## Paso 5 · Obtener el firmware GHI exacto para simulación

Crea localmente `.tools/ghi-debug/` y descarga desde la fuente oficial este archivo, conservando su nombre:
[micropython-esp32-generic-uart0-v1.29.0-16-g201fc48cf9.bin](https://raw.githubusercontent.com/ghi-electronics/micropython-vsc-extension/main/docs/firmware/micropython-esp32-generic-uart0-v1.29.0-16-g201fc48cf9.bin).
Destino: `.tools/ghi-debug/micropython-esp32-generic-uart0-v1.29.0-16-g201fc48cf9.bin`.
Variante: **ESP32_GENERIC_UART0**; versión **1.29.0-16-g201fc48cf9**; tamaño **1829024 bytes**.
MD5 esperado: **0039EDD36E557B0BD1F5DB20CDF97502**; compararlo con el [índice oficial](https://raw.githubusercontent.com/ghi-electronics/micropython-vsc-extension/main/docs/firmware/micropython_firmware.json).
Verifica tamaño y MD5 mediante herramientas disponibles en el SO; no aceptes una descarga HTML como firmware.
`MicroPython-debug/wokwi.toml` ya apunta a ese archivo mediante `../.tools/ghi-debug/` y usa RFC2217 4000.
Esto selecciona firmware del simulador: **no flashear una placa física**. GDB y su puerto 3333 no intervienen.
El firmware normal 1.27 de `MicroPython/` queda separado; no sustituirlo con el de GHI.
**Pide confirmación:** ruta, tamaño y checksum coincidentes.

## Paso 6 · Aplicar el ajuste local de GHI 0.2.2

Copiar el repositorio NO aplica este parche: modifica un archivo de la extensión instalada en el equipo destino.
Detén la depuración antes de editar. Localiza la instalación activa de GHI **0.2.2**, sin reutilizar el usuario/ruta del profesor.
En Linux local suele estar bajo `~/.vscode/extensions/ghielectronics.micropython-debugger-0.2.2/`.
Antes de tocar `out/debugSession.js`, guarda una copia sin modificar en `.tools/ghi-debug/debugSession.original.js`; no sobrescribas un backup existente sin revisarlo.
Si ya contiene el bucle de tres intentos, comprueba su contenido y **no lo reapliques**. Si la versión difiere, revisar primero: nada de sustituciones ciegas.
Dentro de **`launchUart`**, localiza la reapertura posterior al reinicio: `await this.link.open(port, baud);` y después `this.attachEvents();`.
Sustituye únicamente la llamada inmediata siguiente `await this.link.conditions(4 /* Cond.Attached */, 0);` por este bloque exacto del ajuste probado:

```js
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
```

El bloque está tras `this.attachEvents()` y antes de consultar `this.link.capabilities()`; no cambiar otras llamadas de conexión.
Son hasta tres intentos, con 250 ms entre fallos. Cada petición conserva el timeout de 5 s definido en `DeviceLink.request`.
Una actualización/reinstalación de la extensión puede pisar el parche; el backup es local y tampoco viene incluido por copiar Git.
Ejecuta **Developer: Reload Window** después de guardarlo y **antes** de iniciar la simulación.
**Pide confirmación:** versión, backup, bloque localizado y ventana recargada.

## Paso 7 · Iniciar Wokwi desde su panel

1. Cierra depuraciones anteriores, conexiones `mpremote` y cualquier puente iniciado manualmente.
2. En el icono lateral Wokwi, usa **Select Config File** → `MicroPython-debug/wokwi.toml`.
3. Pulsa **Start Simulation**, NO **Start with Debugger**: este último corresponde al flujo GDB.
4. Mantén el simulador visible y sin pausar; una pestaña oculta puede pausar Wokwi.

Montaje: DevKit C V4 + OLED SSD1306; GND→GND.1, VCC→3V3, SDA→21 y SCL→22.
La pantalla puede estar negra antes de ejecutar `show()`; no demuestra una avería.
**Pide confirmación:** configuración seleccionada y montaje visible.

## Paso 8 · Lanzar el perfil OLED remoto y esperar el puente

Abre `MicroPython-debug/oled_demo.py`; pon breakpoint en **línea 29**, el `print` posterior a `mostrar_contador`.
En **Ejecutar y depurar**, selecciona **OLED — depuración REMOTA GHI (no Python del PC)**.
Pulsa el triángulo **de ese panel, junto al selector**; no «Depurar archivo Python» del editor.
El perfil lanza automáticamente las tareas: puente con `--ensure --recover-stale`, seguido de validación `--check`.
Espera **Puente activo.** y la comprobación de PID, PTY y propietario. Conserva abierta la terminal de la tarea.
No lances otro puente manual ni `mpremote`: GHI transfiere la demo y el controlador mediante `sync: true`.
El perfil usa UART a 115200 y `.tools/wokwi-ghi-uart`; un enlace presente no demuestra que el puente esté vivo.
Un mensaje de reintento **(1/3)** puede ser normal durante el arranque; espera el resultado final.
**Pide confirmación:** tareas aprobadas y estado del depurador. Si aparece **Paused on entry**, pulsa F5 para continuar.

## Paso 9 · Demostrar la conexión y avanzar

Confirma juntos: **Paused on breakpoint**, línea 29, Variables y OLED actualizada.
En locales deben aparecer `contador = 1`, `_ = 0` y `display` como objeto `SSD1306_I2C`.
Pila esperada: `ejecutar_demo` en línea 29 y `<module>` en línea 33.
OLED: «Demo OLED», «Sergio: ESP32 OK» y «vuelta 1». La pausa ocurre DESPUÉS de `show()`.
GHI mapea la entrada local `oled_demo.py` al `main.py` remoto; ese nombre en el registro remoto es esperable.
F5 continúa al siguiente breakpoint; F10 avanza por líneas sin entrar en las llamadas; F11 permite entrar en una función.
Antes de continuar pide predecir el siguiente contador; después comparar pantalla y variables. La demo tiene tres vueltas, sin `sleep`.
No basta ver Variables: la combinación de adaptador remoto, pila y pantalla distingue este éxito de un depurador local.

## Diagnóstico dirigido

| Síntoma | Acción de la IA |
| --- | --- |
| `debugpy/launcher` o error `machine` del PC | Se ejecuta CPython local: detener y seleccionar el perfil remoto del panel. No `pip install machine`. |
| Tipo `micropython` no reconocido | Revisar GHI en esta ventana/perfil y recarga; no sustituir por adaptador Python/C++. |
| Falla `preLaunchTask` | NO elegir **Debug Anyway**. Leer terminal de tareas y corregir antes de lanzar. |
| PTY obsoleto o enlace existente | `--check` verifica propietario; `--recover-stale` solo recupera restos propios documentados de un PID inexistente. No abrir ni borrar PTY/enlaces ajenos. |
| `Lost connection to the board` | Aviso genérico, no prueba de fallo USB: revisar Debug Console, firmware, parche, puente y simulación visible. |
| Pantalla negra o imagen anterior | Si aún no pasó `show()`, es normal; comprobar breakpoint 29 antes de cambiar cableado. |
| Breakpoint de nivel superior no se detiene | GHI tiene limitaciones de pausa en código de módulo; usar las funciones de la demo proporcionada. |
| Detener/iniciar Wokwi o recargar ventana | Terminar sesión/tarea del puente anterior y relanzar el perfil para crear/validar el enlace; no asumir persistencia. |

## Aceptación y continuidad

- [ ] Versiones, archivos, firmware y checksum registrados en el equipo destino.
- [ ] Parche local revisado, backup conservado y ventana recargada.
- [ ] Inicio normal Wokwi; tareas automáticas y comprobación del puente aprobadas.
- [ ] Pausa remota en línea 29, locales, pila y «vuelta 1» coinciden; F5 alcanza la siguiente vuelta.
- [ ] Luka explica por qué `show()` precede al breakpoint y por qué Python del PC no maneja esta OLED.

Al terminar, detén la depuración y la tarea del puente antes de detener Wokwi. El almacenamiento simulado es volátil; GHI resincroniza al lanzar.
Fallback opcional: seleccionar `MicroPython/wokwi.toml` y seguir la guía normal `MicroPython/GUIA-AGENTE-LUKA.md` (no incluida en este repositorio; pedirla al profesor), con su firmware y carga `mpremote`, después de liberar el puente.
La enseñanza sigue por pistas: funciones, variables, bucles y predicción; este éxito no autoriza generar lógica de robots.

## Fuentes y alcance

- [README local y evidencia del 16/10/2026](README.md), [perfiles](../.vscode/launch.json), [tareas](../.vscode/tasks.json) y [puente](../tools/wokwi_debug_bridge.py).
- [GHI: documentación y código oficiales](https://github.com/ghi-electronics/micropython-vsc-extension) y [índice oficial de firmware](https://raw.githubusercontent.com/ghi-electronics/micropython-vsc-extension/main/docs/firmware/micropython_firmware.json).
- [Wokwi: configuración y RFC2217](https://docs.wokwi.com/vscode/project-config). La integración y el parche descritos son locales, no una garantía oficial GHI para Wokwi.
