"""Controlador de la calculadora pensional.

Coordina la comunicación entre las vistas (consola y GUI de Kivy)
y el modelo de negocio (src.model.logica_pension).

Toda la lógica de cálculo vive en el modelo; este módulo solo:
- Construye los objetos de datos a partir de entradas crudas.
- Traduce las excepciones de negocio a mensajes amigables.
- Formatea los resultados para mostrarlos al usuario.
"""

import sys
import os
from typing import List

# Permite ejecutar este módulo desde cualquier ubicación (consola, GUI,
# pruebas o empaquetado con PyInstaller) sin depender del Sources Root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model import logica_pension
from model.logica_pension import DatosPension, ResultadoPension


# Mensajes amigables asociados a cada excepción de negocio.
# Las vistas los muestran tal cual al usuario.
MENSAJES_ERROR = {
    logica_pension.SemanasInsuficientes:
        "No tiene derecho a pensión aún: se requieren mínimo "
        f"{logica_pension.SEMANAS_MINIMAS} semanas cotizadas.",
    logica_pension.SemanasNegativas:
        "Las semanas cotizadas no pueden ser negativas.",
    logica_pension.IblCero:
        "El IBL no puede ser cero: ingrese un ingreso base de "
        "cotización válido.",
    logica_pension.IblNegativo:
        "El IBL no puede ser negativo: verifique los valores de IBC.",
    logica_pension.SalarioMinimoLegalVigenteCero:
        "El salario mínimo legal vigente no puede ser cero.",
    logica_pension.SalarioMinimoNegativo:
        "El salario mínimo legal no puede ser negativo.",
    logica_pension.EdadInsuficiente:
        "No cumple la edad mínima para pensionarse: 57 años para "
        "mujeres y 62 años para hombres.",
    logica_pension.SexoInvalido:
        "El sexo debe ser 'M' (hombre) o 'F' (mujer).",
}

# Mensaje genérico para errores de formato (no de negocio), como texto
# no numérico o campos vacíos; ambas vistas lo reutilizan tal cual.
MENSAJE_ENTRADA_INVALIDA = (
    "Entrada no válida: ingrese solo valores numéricos "
    "(use punto para decimales)."
)


class CalculadoraPensionController:
    """Coordina vistas y modelo para el cálculo pensional."""

    def construir_datos(
        self,
        ibc_ultimos_10: float,
        ibc_toda_vida: float,
        salario_minimo_legal: int,
        semanas_cotizadas: int,
        edad: int,
        sexo: str,
    ) -> DatosPension:
        """Crea un DatosPension a partir de valores ya convertidos.

        Normaliza el sexo (quita espacios y pasa a mayúscula) para que
        a ambas vistas les dé igual si el usuario escribió "m", " M "
        o "M"; la validación de que sea 'M' o 'F' la hace el modelo.
        """
        return DatosPension(
            ibc_ultimos_10=ibc_ultimos_10,
            ibc_toda_vida=ibc_toda_vida,
            salario_minimo_legal=salario_minimo_legal,
            semanas_cotizadas=semanas_cotizadas,
            edad=edad,
            sexo=str(sexo).strip().upper(),
        )

    def calcular(self, datos: DatosPension) -> ResultadoPension:
        """Ejecuta el cálculo delegando en el modelo."""
        return logica_pension.calcular_pension(datos=datos)

    def mensaje_de_error(self, error: Exception) -> str:
        """Devuelve un mensaje amigable para una excepción conocida.

        Recorre MENSAJES_ERROR buscando el primer tipo de excepción
        compatible con `error` (por eso usa isinstance y no una simple
        búsqueda por clave exacta, para cubrir también subclases). Si
        no encuentra ninguna coincidencia, cae al mensaje genérico de
        error inesperado en vez de fallar.
        """
        for tipo_excepcion, mensaje in MENSAJES_ERROR.items():
            if isinstance(error, tipo_excepcion):
                return mensaje
        return f"Ocurrió un error inesperado: {error}"

    def formatear_resultado(self, resultado: ResultadoPension) -> List[str]:
        """Devuelve las líneas de texto listas para mostrar al usuario.

        Método compartido por la consola y la GUI: cada vista decide
        cómo presentar estas líneas (print simple en consola, o texto
        de un Label con formato de miles en la GUI), pero el contenido
        y el orden de la información se definen una sola vez aquí.
        """
        return [
            f"IBL calculado: ${resultado.ibl:,.2f}",
            f"Salarios mínimos (S): {resultado.relacion:.2f}",
            f"Porcentaje base: {resultado.tasa_base:.2f}%",
            f"Semanas adicionales: {resultado.semanas_adicionales}",
            f"Incremento: {resultado.incremento:.2f}%",
            f"Porcentaje total: {resultado.tasa_total:.2f}%",
            f"PENSIÓN ESTIMADA: ${resultado.pension:,.2f}",
        ]