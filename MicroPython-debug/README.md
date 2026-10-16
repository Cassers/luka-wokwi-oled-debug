# Prueba experimental: breakpoints Python en Wokwi con GHI

Esta prueba conecta MicroPython Debugger de GHI al ESP32 simulado de Wokwi. La extensión documenta hardware físico; esta combinación con Wokwi sigue siendo experimental y utiliza un ajuste local. Sergio confirmó el flujo completo desde VS Code el 16 de octubre de 2026: pausa en `oled_demo.py:29`, variables locales, pila de llamadas y OLED mostrando «vuelta 1» con `contador = 1`.

## Qué se preparó

- Extensión instalada: `ghielectronics.micropython-debugger` 0.2.2.
- Firmware específico `ESP32_GENERIC_UART0` de GHI, versión `1.29.0-16-g201fc48cf9`, descargado en `.tools/ghi-debug/`.
- Tamaño comprobado: 1 829 024 bytes. MD5 coincide con el índice oficial: `0039EDD36E557B0BD1F5DB20CDF97502`.
- Circuito de prueba con la misma placa y OLED que el ejemplo normal.
- Puente local RFC2217 → PTY para que GHI encuentre un puerto serie Linux. No conecta con dispositivos USB físicos.
- Dos perfiles Python en `.vscode/launch.json`; el perfil GDB anterior se conserva.

## Pasos para probar

1. Guarda los archivos. Abre en VS Code la **raíz del proyecto**, no solo esta carpeta.
2. Detén la simulación anterior y cualquier sesión de depuración. Cierra conexiones `mpremote` activas.
3. En el panel Wokwi usa **Select Config File** y selecciona **`MicroPython-debug/wokwi.toml`**.
4. Pulsa **Start Simulation**, no **Start with Debugger**. El inicio de GDB no interviene en esta prueba.
5. Mantén visible el panel del simulador: Wokwi puede pausar una pestaña oculta.
6. No necesitas abrir manualmente el puente: los perfiles GHI lo inician como tarea de VS Code al pulsar F5. Si antes abriste uno manualmente, ciérralo con Ctrl+C antes de pasar a este flujo automático.
7. La tarea espera **Puente activo** y luego comprueba su propietario. Deja abierta la terminal de la tarea. El enlace `.tools/wokwi-ghi-uart` solo es válido mientras el puente está funcionando.
8. Abre [main.py](main.py) de esta carpeta y pon un breakpoint en **`contador += 1`**, dentro de la función. Es un diagnóstico del depurador, no una solución a un ejercicio.
9. Abre **Ejecutar y depurar**. Selecciona **MicroPython GHI — prueba Python en Wokwi (experimental)** y pulsa **F5**.
10. Si se detiene al entrar, pulsa **F5** para llegar al breakpoint. Comprueba que aparece `contador` en Variables. Usa **F10** para avanzar.

La extensión debería transferir el código por su propio protocolo; **no uses `mpremote` en paralelo**. La simulación UART de GHI no ofrece el REPL habitual del firmware estándar. No esperes necesariamente el indicador `>>>`.

Antes de iniciar GHI, los perfiles ejecutan dos tareas: iniciar el puente en segundo plano y comprobar que está vivo y es dueño del puerto virtual. El inicio puede reutilizar un puente validado y recuperar solo restos propios documentados de un proceso inexistente; no borra enlaces ajenos ni abre un PTY reciclado. Si falla, no elijas «Debug Anyway»: revisa la terminal de la tarea. Recargar VS Code puede terminar el puente; además, Linux puede reutilizar el número `/dev/pts/...` para otra terminal. La presencia de un enlace por sí sola no acredita un puente activo. Un puente iniciado desde las herramientas de la IA tampoco debe considerarse persistente tras terminar su turno.

## Después: intentar el ejemplo OLED

Se añadió una demo independiente: [oled_demo.py](oled_demo.py), con copia del controlador local. El perfil **OLED — depuración REMOTA GHI (no Python del PC)** la despliega sin cambiar los ejercicios ni el ejemplo anterior.

1. Termina cualquier sesión del depurador Python del PC. En una captura anterior el comando contenía `debugpy/launcher`: eso demostraba ejecución local, aunque se viera un breakpoint junto al simulador.
2. Mantén Wokwi con esta configuración experimental y el puente activo. No uses `mpremote` simultáneamente.
3. En **Ejecutar y depurar** (`Ctrl+Shift+D`) selecciona **OLED — depuración REMOTA GHI (no Python del PC)** y pulsa el triángulo de **ese panel**, junto al selector. No uses «Depurar archivo Python» del editor.
4. Pon un breakpoint en la línea 29 de `oled_demo.py`, en el `print` posterior a `mostrar_contador`. Al llegar allí, `show()` ya habrá enviado la imagen de esa vuelta.
5. F5 continúa a la siguiente vuelta; F10 permite avanzar por instrucciones. Si te detienes antes de `show()`, ver la imagen anterior es normal.

La demo reutiliza las llamadas de pantalla probadas en el ejemplo. La sintaxis, el perfil remoto y la copia exacta del controlador se comprobaron; también se confirmó la parada de la demo en el firmware real simulado usando el adaptador UART corregido. La mera presencia de Variables en VS Code no demuestra conexión al ESP32: comprobar el adaptador y el registro de la sesión.

## Ajuste local de GHI 0.2.2 para reiniciar en Wokwi

El adaptador original reabre UART 1,5 segundos después del reinicio e intenta adjuntarse una sola vez. En la prueba medida, ese primer comando se envió antes de que el firmware estuviera listo y no recibió respuesta; un segundo intento sí conectó. Esto producía el aviso genérico «Lost connection to the board».

Se añadió un máximo de tres intentos de adjuntar, con 250 ms entre fallos, únicamente en `launchUart` del archivo instalado `~/.vscode/extensions/ghielectronics.micropython-debugger-0.2.2/out/debugSession.js`. Cada petición conserva su timeout original. Copia anterior: `.tools/ghi-debug/debugSession.original.js`.

Después del ajuste, usar **Developer: Reload Window**, volver a iniciar Wokwi con la configuración experimental y lanzar el perfil OLED. La tarea de VS Code volverá a iniciar el puente cuando haga falta. Una actualización o reinstalación de GHI puede reemplazar este ajuste local; no se cambió la configuración de actualizaciones.

Con la prueba anterior funcionando, termina esa sesión de depuración y selecciona **MicroPython GHI — OLED en Wokwi (experimental)**. Ese perfil transfiere los archivos de `MicroPython/` y ejecuta su `main.py`.

No se ha modificado la lógica del ejemplo OLED. GHI documenta una limitación con breakpoints en código de nivel superior de un módulo: pueden no detenerse. Por eso la primera prueba usa una función. Que funcione el diagnóstico no garantiza todavía todos los breakpoints del ejemplo OLED.

## Si falla

- **Tipo de depuración no reconocido:** comprobar la extensión GHI instalada y, si VS Code lo solicita, recargar la ventana.
- **No existe `.tools/wokwi-ghi-uart`:** iniciar primero el puente y revisar su error. Verificar que Wokwi usa esta configuración y está funcionando.
- **Conexión rechazada:** el puerto 4000 no está disponible. No cambiarlo por un puerto USB ni usar un dispositivo físico como sustituto.
- **Timeout/handshake:** comprobar el firmware GHI seleccionado y que la simulación siga visible y sin pausar. Enviar el texto de la consola de depuración. No aceptar una oferta de flashear hardware para resolver este experimento.
- **El puente indica enlace existente:** puede haber otro puente activo. Cerrar su terminal con Ctrl+C antes de reintentar; no borrar rutas sin comprobar su propietario.
- **Lost connection to the board:** es un aviso genérico de GHI, no prueba de fallo de un cable USB. Comprobar primero el puente, su terminal y el mensaje detallado de Debug Console. En esta sesión se encontró un enlace obsoleto hacia un PTY que ya pertenecía a una terminal fish; se retiró solo ese enlace, sin tocar la terminal ni el dispositivo.
- **Se detiene la simulación:** cerrar el puente con Ctrl+C, volver a iniciar Wokwi y ejecutar de nuevo el puente antes de F5.
- **Falla un breakpoint OLED:** primero repetir el diagnóstico dentro de la función. Conservar el error completo y no cambiar varios componentes a la vez.

El firmware GHI deshabilita el flujo normal de REPL en UART. No combinar las instrucciones de carga estándar de `mpremote` con este perfil.

## Volver a la versión que ya funcionaba

Termina la depuración, cierra el puente con Ctrl+C y detén Wokwi. En **Select Config File** vuelve a **`MicroPython/wokwi.toml`**, pulsa **Start Simulation** y usa la carga normal con `mpremote`. El firmware original y sus archivos permanecen disponibles.

## Verificación y alcance

Se verificaron manifest, checksum del firmware, configuración JSON/TOML y rutas. El puente pasó una prueba local binaria de ida/vuelta con negociación RFC2217 y apertura/reapertura mediante SerialPort de GHI.

Después de corregir el enlace obsoleto, se comprobó la comunicación con el firmware GHI dentro de Wokwi: `PING` respondió `true` y la consulta de capacidades devolvió protocolo 10, 16 breakpoints máximos y payload de 512 bytes.

La prueba posterior ejecutó el método `launchUart` exacto del adaptador corregido, con `DeviceLink` real y sin volver a desplegar archivos (`sync: false`, la demo ya estaba cargada). El primer intento falló; el reintento conectó. El firmware aceptó un breakpoint en `main.py:29` y emitió parada de tipo breakpoint. La consulta de pila devolvió `ejecutar_demo` en línea 29 y `<module>` en línea 33. GHI mapea la entrada local `oled_demo.py` al `main.py` remoto. Al finalizar se retiraron los breakpoints de diagnóstico y se liberó el puerto; el puente de VS Code se mantuvo disponible.

Verificación visual posterior aportada por Sergio: VS Code mostró «Paused on breakpoint» en `oled_demo.py:29`, locales `contador = 1`, `_ = 0` y un objeto `SSD1306_I2C`; la pila mostró `ejecutar_demo()` y `<module>`, y la OLED mostró «Demo OLED», «Sergio: ESP32 OK» y «vuelta 1». Esto confirma la integración de depuración remota y pantalla en este equipo; no garantiza por sí solo otras versiones, otros sistemas ni hardware físico.

Herramientas y firmware descargados viven en `.tools/`, ignorado por Git; deben obtenerse de nuevo en otro PC. El puente es para Linux y utiliza `pyserial`, disponible en el entorno `.venv` del profesor.

Fuentes: [GHI MicroPython Debugger](https://github.com/ghi-electronics/micropython-vsc-extension), [índice de firmware](https://raw.githubusercontent.com/ghi-electronics/micropython-vsc-extension/main/docs/firmware/micropython_firmware.json), [configuración y RFC2217 de Wokwi](https://docs.wokwi.com/vscode/project-config).
