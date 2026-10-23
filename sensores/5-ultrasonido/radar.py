# Sensor 5 · HC-SR04: el radar de vampiros.
# Señal de PULSOS: la distancia se mide por cuánto dura un pulso en ECHO.
from machine import time_pulse_us
import time
from machine import Pin, I2C
import ssd1306


def preparar_pantalla():
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    return ssd1306.SSD1306_I2C(128, 64, i2c)


def preparar_radar():
    trig = Pin(32, Pin.OUT, value=0)
    echo = Pin(33, Pin.IN)
    return trig, echo


def medir_cm(trig, echo):
    trig.value(1)       # 1. un disparo de 10 microsegundos
    time.sleep_us(10)
    trig.value(0)
    duracion = time_pulse_us(echo, 1, 30000)  # 2. cuánto dura ECHO en 1
    if duracion < 0:
        return -1        # no volvió el eco
    return duracion / 58  # 3. el sonido va y vuelve: 58 µs por centímetro


def mostrar(display, cm):
    display.fill(0)
    display.text("Radar", 44, 0, 1)
    if cm < 0:
        display.text("Sin eco", 36, 28, 1)
    else:
        display.text("%d cm" % int(cm), 44, 28, 1)
        if cm < 50:
            display.text("Vampiro cerca!", 8, 48, 1)
    display.show()


def main():
    display = preparar_pantalla()
    trig, echo = preparar_radar()
    for vuelta in range(300):
        cm = medir_cm(trig, echo)
        mostrar(display, cm)  # breakpoint aquí
        time.sleep_ms(200)


if __name__ == "__main__":
    main()
