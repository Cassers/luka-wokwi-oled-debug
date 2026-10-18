# Archivo de práctica de Luka: ruta de ejercicios de la guía (sección «Ruta de práctica»).
# Cambia solo lo que está DENTRO de practica(). El resto prepara la pantalla.
# Se ejecuta en el ESP32 simulado con el perfil «Práctica OLED — REMOTA GHI».
import time
from machine import Pin, I2C
import ssd1306


def preparar_pantalla():
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    return ssd1306.SSD1306_I2C(128, 64, i2c)


def practica(display):
    # Reemplaza estas líneas por el código de la práctica que estés haciendo.
    display.fill(0)
    display.text("Feliz Halloween", 0, 0, 1)
    display.text("Tu nombre", 0, 20, 1)
    display.show()


def main():
    display = preparar_pantalla()
    practica(display)
    print("Práctica terminada")


if __name__ == "__main__":
    main()
