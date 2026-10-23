# Sensor 2 · PIR: el detector de fantasmas.
# Señal DIGITAL: el sensor pone su salida en 1 cuando detecta movimiento.
import time
from machine import Pin, I2C
import ssd1306


def preparar_pantalla():
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    return ssd1306.SSD1306_I2C(128, 64, i2c)


def preparar_pir():
    return Pin(26, Pin.IN)


def mostrar(display, hay_movimiento, sustos):
    display.fill(0)
    display.text("Detector", 32, 0, 1)
    if hay_movimiento:
        display.text("FANTASMA!", 28, 24, 1)
    else:
        display.text("Todo tranquilo", 8, 24, 1)
    display.text("Sustos: %d" % sustos, 0, 48, 1)
    display.show()


def main():
    display = preparar_pantalla()
    pir = preparar_pir()
    sustos = 0
    antes = 0
    for vuelta in range(600):  # unos 60 segundos
        ahora = pir.value()
        if antes == 0 and ahora == 1:  # flanco de subida: empieza un movimiento
            sustos += 1  # breakpoint aquí
        mostrar(display, ahora == 1, sustos)
        antes = ahora
        time.sleep_ms(100)


if __name__ == "__main__":
    main()
