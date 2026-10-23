# Sensor 3 · Potenciómetro: la perilla del grito.
# Señal ANALÓGICA: el voltaje puede tener muchos valores entre 0 y 3,3 V.
from machine import ADC
import time
from machine import Pin, I2C
import ssd1306


def preparar_pantalla():
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    return ssd1306.SSD1306_I2C(128, 64, i2c)


def preparar_perilla():
    adc = ADC(Pin(34))
    adc.atten(ADC.ATTN_11DB)  # permite leer todo el rango, de 0 a unos 3,3 V
    return adc


def leer_porcentaje(adc):
    crudo = adc.read_u16()  # número de 0 a 65535
    return crudo * 100 // 65535


def mostrar(display, porcentaje):
    display.fill(0)
    display.text("Volumen grito", 12, 0, 1)
    display.text("%d %%" % porcentaje, 52, 20, 1)
    display.rect(4, 40, 120, 12, 1)
    display.fill_rect(4, 40, porcentaje * 120 // 100, 12, 1)
    display.show()


def main():
    display = preparar_pantalla()
    adc = preparar_perilla()
    for vuelta in range(300):  # unos 60 segundos
        porcentaje = leer_porcentaje(adc)
        mostrar(display, porcentaje)  # breakpoint aquí
        time.sleep_ms(200)


if __name__ == "__main__":
    main()
