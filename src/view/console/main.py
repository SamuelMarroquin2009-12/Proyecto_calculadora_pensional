"""Interfaz de consola (CLI) de la calculadora pensional.

Uso:
    python src/view/console/main.py
"""

import sys
import os

# Permite ejecutar el archivo directamente sin configurar Sources Root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from controller.pension_controller import (
    CalculadoraPensionController,
    MENSAJE_ENTRADA_INVALIDA,
)


def solicitar_numero(mensaje):
    """Solicita un número al usuario; reintenta hasta obtenerlo."""
    while True:
        entrada = input(mensaje).strip()
        if not entrada:
            print("  >> El campo no puede estar vacío. Intente de nuevo.")
            continue
        try:
            return float(entrada)
        except ValueError:
            print("  >> Entrada no válida: ingrese un valor numérico.")


def solicitar_entero(mensaje):
    """Solicita un entero al usuario; reintenta hasta obtenerlo."""
    while True:
        valor = solicitar_numero(mensaje)
        if valor == int(valor):
            return int(valor)
        print("  >> Entrada no válida: ingrese un número entero.")


def solicitar_sexo():
    """Solicita el sexo (M/F); reintenta hasta obtenerlo."""
    while True:
        sexo = input("Sexo (M/F): ").strip().upper()
        if sexo in ("M", "F"):
            return sexo
        print("  >> Entrada no válida: ingrese 'M' para hombre o 'F' para mujer.")


def solicitar_datos(controlador):
    print("\nIngrese los siguientes datos:\n")

    ibc_ultimos_10 = solicitar_numero("IBC de los últimos 10 años: ")
    ibc_toda_vida = solicitar_numero("IBC de toda la vida laboral: ")
    salario_minimo_legal = solicitar_entero("Salario mínimo legal vigente: ")
    semanas_cotizadas = solicitar_entero("Semanas cotizadas: ")
    edad = solicitar_entero("Edad: ")
    sexo = solicitar_sexo()

    return controlador.construir_datos(
        ibc_ultimos_10, ibc_toda_vida, salario_minimo_legal,
        semanas_cotizadas, edad, sexo
    )


def mostrar_resultados(controlador, resultado):
    print("\n" + "=" * 50)
    print("             RESULTADOS")
    print("=" * 50)
    for linea in controlador.formatear_resultado(resultado):
        print(linea)
    print("=" * 50)


def main():
    controlador = CalculadoraPensionController()

    print("=" * 50)
    print("       CALCULADORA PENSIONAL")
    print("=" * 50)

    try:
        datos = solicitar_datos(controlador)
        resultado = controlador.calcular(datos)
        mostrar_resultados(controlador, resultado)
    except ValueError:
        print("\nERROR: " + MENSAJE_ENTRADA_INVALIDA)
    except Exception as error:
        print("\nERROR: " + controlador.mensaje_de_error(error))


if __name__ == "__main__":
    main()
