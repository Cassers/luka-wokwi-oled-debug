# Sensor 4 · Fotorresistencia (LDR): luz de luna.
# Da DOS señales: AO es analógica (cuánta luz) y DO es digital (¿está oscuro?).
from machine import ADC
import time
from machine import Pin, I2C
import ssd1306


def preparar_pantalla():
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    return ssd1306.SSD1306_I2C(128, 64, i2c)


def preparar_sensor():
    ao = ADC(Pin(35))
    ao.atten(ADC.ATTN_11DB)
    do = Pin(27, Pin.IN)
    return ao, do


def mostrar(display, crudo, oscuro):
    display.fill(0)
    display.text("Luz de luna", 20, 0, 1)
    display.text("AO: %d" % crudo, 0, 20, 1)
    if oscuro:
        display.text("Noche: salen", 0, 40, 1)
        display.text("los vampiros", 0, 52, 1)
    else:
        display.text("Dia: a salvo", 0, 40, 1)
    display.show()


def main():
    display = preparar_pantalla()
    ao, do = preparar_sensor()
    for vuelta in range(300):
        crudo = ao.read_u16()  # mucha luz = número bajo, poca luz = número alto
        oscuro = do.value() == 1  # DO se pone en 1 cuando está oscuro
        mostrar(display, crudo, oscuro)  # breakpoint aquí
        time.sleep_ms(200)


if __name__ == "__main__":
    main()
