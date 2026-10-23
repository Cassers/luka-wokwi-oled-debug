# 🐞 RETO · CAZA EL BICHO
# Este programa tiene UN error escondido. Síntoma: OSError(116): el sensor «no contesta».
# No lo compares con termometro.py: encuéntralo con el depurador
# (breakpoints, Variables y Watch). Pistas en la guía.
# Chip 1 · DHT22: el termómetro embrujado.
# Protocolo de UN cable: el sensor y el ESP32 se turnan para hablar por un solo pin.
import time
import dht
from machine import Pin, I2C
import ssd1306


def preparar_pantalla():
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    return ssd1306.SSD1306_I2C(128, 64, i2c)


def preparar_sensor():
    # El DHT22 solo necesita saber en qué pin está su cable de datos.
    return dht.DHT22(Pin(5))


def leer(sensor):
    sensor.measure()  # pide una medida nueva al sensor
    return sensor.temperature(), sensor.humidity()


def mostrar(display, temperatura, humedad):
    display.fill(0)
    display.text("Termometro", 24, 0, 1)
    display.text("Temp: %.1f C" % temperatura, 0, 20, 1)
    display.text("Humedad: %d %%" % humedad, 0, 32, 1)
    if temperatura > 30:
        display.text("Calor de caldero", 0, 52, 1)
    display.show()


def main():
    display = preparar_pantalla()
    sensor = preparar_sensor()
    for vuelta in range(30):
        temperatura, humedad = leer(sensor)
        mostrar(display, temperatura, humedad)  # breakpoint aquí para ver los valores
        time.sleep(2)  # el DHT22 necesita 2 segundos entre medidas


if __name__ == "__main__":
    main()
