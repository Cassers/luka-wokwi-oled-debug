# Demo de diagnóstico OLED para Sergio; no es un ejercicio del estudiante.
# Requiere MicroPython en el destino y el montaje I2C del ejemplo existente.
# Sintaxis comprobable en PC; ejecución con adaptador GHI aún no confirmada.
from machine import Pin, I2C
import ssd1306


def preparar_pantalla():
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    display = ssd1306.SSD1306_I2C(128, 64, i2c)
    return display


def mostrar_contador(display, contador):
    display.fill(0)
    display.text("Demo OLED", 0, 0, 1)
    display.text("Sergio: ESP32 OK", 0, 20, 1)
    display.text("vuelta %d" % contador, 0, 40, 1)
    display.show()


def ejecutar_demo():
    display = preparar_pantalla()
    contador = 0
    for _ in range(3):
        contador += 1
        mostrar_contador(display, contador)
        # Breakpoint en el print: show() ya terminó y contador está actualizado.
        print("vuelta", contador, "- OLED OK")


if __name__ == "__main__":
    ejecutar_demo()
