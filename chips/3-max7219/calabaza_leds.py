# Chip 3 · MAX7219: la calabaza de LEDs (matriz de 8 × 8).
# Protocolo SPI: reloj (18), datos (23) y un pin de "te hablo a ti" llamado CS (5).
import time
from machine import Pin, SPI

REG_DECODIFICAR = 0x09  # 0 = dibujamos punto por punto, sin números automáticos
REG_BRILLO = 0x0A       # de 0 (tenue) a 15 (máximo)
REG_FILAS = 0x0B        # cuántas filas usar: 7 = las 8 (de 0 a 7)
REG_ENCENDIDO = 0x0C    # 1 = encendido
REG_PRUEBA = 0x0F       # 1 = enciende todo para probar

CALABAZA = [
    0b00011000,
    0b01111110,
    0b11111111,
    0b10111101,
    0b11111111,
    0b10100101,
    0b11011011,
    0b01111110,
]

FANTASMA = [
    0b00111100,
    0b01111110,
    0b11011011,
    0b11111111,
    0b11111111,
    0b11111111,
    0b11111111,
    0b10101010,
]


def preparar_spi():
    spi = SPI(2, baudrate=1000000, sck=Pin(18), mosi=Pin(23))
    cs = Pin(5, Pin.OUT, value=1)  # CS en 1 = "no te estoy hablando"
    return spi, cs


def escribir(spi, cs, registro, valor):
    cs.value(0)                       # 1. levantar la mano: "te hablo a ti"
    spi.write(bytes([registro, valor]))  # 2. enviar dirección del registro y valor
    cs.value(1)                       # 3. bajar la mano: el chip guarda el dato


def iniciar(spi, cs):
    escribir(spi, cs, REG_PRUEBA, 0)
    escribir(spi, cs, REG_FILAS, 7)
    escribir(spi, cs, REG_DECODIFICAR, 0)
    escribir(spi, cs, REG_BRILLO, 3)
    escribir(spi, cs, REG_ENCENDIDO, 1)


def dibujar(spi, cs, filas):
    for numero in range(8):
        escribir(spi, cs, numero + 1, filas[numero])  # las filas son los registros 1 a 8


def main():
    spi, cs = preparar_spi()
    iniciar(spi, cs)
    for vez in range(6):
        dibujar(spi, cs, CALABAZA)  # breakpoint aquí
        time.sleep(1)
        dibujar(spi, cs, FANTASMA)
        time.sleep(1)
    print("Fin del espectáculo")


if __name__ == "__main__":
    main()
