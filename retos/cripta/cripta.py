# Reto · La cripta: varios chips en un mismo circuito.
# Empiezas solo con la OLED. En cada PASO de la guía:
#   1) agregas una pieza y sus cables en diagram.json,
#   2) pegas un bloque de código donde dice «PASO n»,
#   3) reinicias la simulación y compruebas antes de seguir.
import time
from machine import Pin, I2C
import ssd1306


def preparar_bus():
    # Un solo bus I2C para TODOS los chips I2C del circuito.
    return I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)


# PASO 1 · pega aquí preparar_boton()


# PASO 2 · pega aquí despertar_mpu() y leer_inclinacion()


# PASO 3 · pega aquí preparar_perilla() y leer_porcentaje()


def main():
    i2c = preparar_bus()
    print("Chips en el bus I2C:", i2c.scan())  # Paso 0: [60]
    display = ssd1306.SSD1306_I2C(128, 64, i2c)
    display.fill(0)
    display.text("La cripta", 28, 0, 1)
    display.text("Paso 0: OK", 0, 28, 1)
    display.show()

    # PASOS 1, 2 y 3 · prepara aquí cada pieza nueva

    for vuelta in range(600):  # unos 60 segundos
        # PASO 4 · el reto: lee las piezas y dibuja en la OLED
        time.sleep_ms(100)


if __name__ == "__main__":
    main()
