# 🐞 RETO · CAZA EL BICHO
# Este programa tiene UN error escondido. Síntoma: OSError: [Errno 19] ENODEV al despertar el chip (aunque scan() sí lo ve).
# No lo compares con varita.py: encuéntralo con el depurador
# (breakpoints, Variables y Watch). Pistas en la guía.
# Chip 2 · MPU6050: la varita mágica.
# Protocolo I2C: comparte los cables SDA (21) y SCL (22) con la OLED.
# Cada chip tiene su propia dirección en el bus.
import time
from machine import Pin, I2C
import ssd1306

MPU = 0x69          # dirección del MPU6050 en el bus I2C
REG_ENCENDIDO = 0x6B  # registro PWR_MGMT_1: 0 = despierto
REG_ACELERACION = 0x3B  # aquí empiezan los 6 bytes de aceleración X, Y, Z


def preparar_bus():
    return I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)


def despertar_mpu(i2c):
    # Al encender, el MPU6050 está dormido: se despierta escribiendo 0 en su registro.
    i2c.writeto_mem(MPU, REG_ENCENDIDO, b"\x00")


def con_signo(alto, bajo):
    # Junta dos bytes en un número que puede ser negativo (−32768 a 32767).
    valor = (alto << 8) | bajo
    if valor > 32767:
        valor -= 65536
    return valor


def leer_aceleracion(i2c):
    datos = i2c.readfrom_mem(MPU, REG_ACELERACION, 6)
    ax = con_signo(datos[0], datos[1]) / 16384  # 16384 = 1 g en el rango de ±2 g
    ay = con_signo(datos[2], datos[3]) / 16384
    az = con_signo(datos[4], datos[5]) / 16384
    return ax, ay, az


def mostrar(display, ax, ay):
    display.fill(0)
    display.text("Varita magica", 12, 0, 1)
    x = 60 + int(ax * 50)
    y = 34 + int(ay * 20)
    x = max(0, min(120, x))
    y = max(12, min(56, y))
    display.fill_rect(x, y, 8, 8, 1)  # el fantasma se mueve al inclinar
    display.show()


def main():
    i2c = preparar_bus()
    print("Chips encontrados:", i2c.scan())  # debería mostrar [60, 104]
    display = ssd1306.SSD1306_I2C(128, 64, i2c)
    despertar_mpu(i2c)
    for vuelta in range(100):
        ax, ay, az = leer_aceleracion(i2c)
        mostrar(display, ax, ay)  # breakpoint aquí para ver ax, ay
        time.sleep(0.2)


if __name__ == "__main__":
    main()
