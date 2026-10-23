# Sensor 1 · Botón: el caldero de ingredientes.
# Señal DIGITAL: solo hay dos estados, 1 (suelto) o 0 (pulsado).
import time
from machine import Pin, I2C
import ssd1306


def preparar_pantalla():
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    return ssd1306.SSD1306_I2C(128, 64, i2c)


def preparar_boton():
    # PULL_UP: una resistencia interna deja el pin en 1 mientras nadie pulsa.
    # Al pulsar, el botón une el pin con GND y se lee 0.
    return Pin(13, Pin.IN, Pin.PULL_UP)


def mostrar(display, ingredientes):
    display.fill(0)
    display.text("Caldero", 36, 0, 1)
    display.text("Ingredientes: %d" % ingredientes, 0, 28, 1)
    if ingredientes >= 5:
        display.text("Pocion lista!", 12, 48, 1)
    display.show()


def main():
    display = preparar_pantalla()
    boton = preparar_boton()
    ingredientes = 0
    antes = 1
    mostrar(display, ingredientes)
    for vuelta in range(3000):  # unos 60 segundos
        ahora = boton.value()
        if antes == 1 and ahora == 0:  # justo en el momento de pulsar
            ingredientes += 1
            mostrar(display, ingredientes)  # breakpoint aquí
        antes = ahora
        time.sleep_ms(20)  # 20 ms de pausa también evitan los rebotes del botón


if __name__ == "__main__":
    main()
