# 🐞 RETO · CAZA EL BICHO
# Este programa tiene UN error escondido. Síntoma: el programa se cae con IndexError justo después de buscar sensores.
# No lo compares con caldero_termico.py: encuéntralo con el depurador
# (breakpoints, Variables y Watch). Pistas en la guía.
# Sensor 6 · DS18B20: el termómetro del caldero.
# BUS 1-Wire: un solo cable de datos donde pueden colgar varios sensores,
# cada uno con un número de serie único (su ROM).
import onewire
import ds18x20
import time
from machine import Pin, I2C
import ssd1306


def preparar_pantalla():
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    return ssd1306.SSD1306_I2C(128, 64, i2c)


def preparar_sensores():
    bus = onewire.OneWire(Pin(4))
    sensores = ds18x20.DS18X20(bus)
    roms = sensores.scan()  # lista con el número de serie de cada sensor
    return sensores, roms


def leer(sensores, rom):
    sensores.convert_temp()  # orden: «midan la temperatura»
    time.sleep_ms(750)       # el DS18B20 tarda hasta 750 ms en medir
    return sensores.read_temp(rom)


def mostrar(display, temperatura):
    display.fill(0)
    display.text("Caldero", 36, 0, 1)
    display.text("%.1f C" % temperatura, 40, 28, 1)
    if temperatura >= 100:
        display.text("Hierve!", 36, 48, 1)
    display.show()


def main():
    display = preparar_pantalla()
    sensores, roms = preparar_sensores()
    print("Sensores encontrados:", len(roms))
    for rom in roms:
        print("  ROM:", rom.hex())
    if not roms:
        display.fill(0)
        display.text("Sin sensor", 24, 28, 1)
        display.show()
        return
    for vuelta in range(60):
        temperatura = leer(sensores, roms[1])
        mostrar(display, temperatura)  # breakpoint aquí


if __name__ == "__main__":
    main()
