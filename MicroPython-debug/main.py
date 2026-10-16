# Diagnóstico del depurador; no es un ejercicio ni lógica de los robots.
# Poner un breakpoint en la línea que incrementa contador.
def comprobar_debugger():
    contador = 0
    for paso in range(3):
        contador += 1
        print("Prueba debugger:", paso, contador)
    return contador


resultado = comprobar_debugger()
print("Prueba terminada:", resultado)
