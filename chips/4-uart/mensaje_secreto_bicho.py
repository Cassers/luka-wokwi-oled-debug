# 🐞 RETO · CAZA EL BICHO
# Este programa tiene UN error escondido. Síntoma: cada mensaje llega con una vuelta de retraso.
# No lo compares con mensaje_secreto.py: encuéntralo con el depurador
# (breakpoints, Variables y Watch). Pistas en la guía.
# Chip 4 · UART: el mensaje secreto.
# Protocolo UART (puerto serie): un cable para enviar (TX, 17) y otro para recibir (RX, 16).
# En este circuito el cable sale del 17 y vuelve a entrar por el 16: el ESP32 se habla a sí mismo.
# Con dos placas reales, el TX de una va al RX de la otra (y comparten GND).
import time
from machine import Pin, I2C, UART
import ssd1306


def preparar_pantalla():
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    return ssd1306.SSD1306_I2C(128, 64, i2c)


def preparar_uart():
    # UART 2, velocidad 9600 bits por segundo. Los dos lados deben usar la MISMA velocidad.
    return UART(2, baudrate=9600, tx=17, rx=16)


def enviar(uart, texto):
    uart.write(texto)


def recibir(uart):
    time.sleep(0.1)  # dar tiempo a que lleguen las letras
    if uart.any():
        return uart.read().decode()
    return ""


def mostrar(display, enviado, recibido):
    display.fill(0)
    display.text("Mensaje secreto", 4, 0, 1)
    display.text("Envie: " + enviado, 0, 24, 1)
    display.text("Llego: " + recibido, 0, 40, 1)
    display.show()


def main():
    display = preparar_pantalla()
    uart = preparar_uart()
    for palabra in ["BOO", "Dulce", "Truco"]:
        llegada = recibir(uart)
        enviar(uart, palabra)
        mostrar(display, palabra, llegada)  # breakpoint aquí
        time.sleep(1)


if __name__ == "__main__":
    main()
