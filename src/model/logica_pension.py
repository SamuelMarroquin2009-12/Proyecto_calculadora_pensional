"""Lógica de negocio de la calculadora pensional.

Régimen de Prima Media - Pensión de Vejez en Colombia.

Este módulo contiene toda la lógica de cálculo y validación.
Es compartido por la interfaz de consola y la interfaz gráfica (Kivy),
por lo que no debe depender de ninguna librería de interfaz.
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Constantes del régimen (Régimen de Prima Media - Colombia).
# Centralizarlas aquí evita "números mágicos" repartidos por el código
# y permite ajustarlas en un solo lugar si cambia la normativa.
# ---------------------------------------------------------------------------

SEMANAS_MINIMAS = 1300              # Semanas cotizadas mínimas para tener derecho a pensión.
SEMANAS_POR_INCREMENTO = 50         # Tamaño de cada bloque de semanas adicionales.
INCREMENTO_PORCENTUAL = 1.5         # Puntos que sube la tasa por cada bloque completo.

TASA_REEMPLAZO_INICIAL = 65.5       # Porcentaje base de reemplazo antes de ajustes.
FACTOR_REDUCCION_POR_SALARIO = 0.5  # Cuánto baja la tasa por cada salario mínimo de IBL.
TASA_REEMPLAZO_MINIMA = 55          # Piso legal de la tasa de reemplazo.
TASA_REEMPLAZO_MAXIMA = 80          # Techo legal de la tasa de reemplazo.

EDAD_MINIMA_MUJER = 57              # Edad mínima de pensión para mujeres.
EDAD_MINIMA_HOMBRE = 62             # Edad mínima de pensión para hombres.


@dataclass
class DatosPension:
    """Agrupa los datos necesarios para realizar el cálculo de la pensión."""

    ibc_ultimos_10: float
    ibc_toda_vida: float
    salario_minimo_legal: int
    semanas_cotizadas: int
    edad: int
    sexo: str


@dataclass
class ResultadoPension:
    """Agrupa los resultados del cálculo de la pensión."""

    ibl: float
    relacion: float
    tasa_base: float
    semanas_adicionales: int
    incremento: float
    tasa_total: float
    pension: float


# ---------------------------------------------------------------------------
# Excepciones de negocio.
#
# Todas heredan de ErrorCalculoPension para que las vistas (consola y GUI)
# puedan capturar un único tipo específico en lugar de "except Exception",
# tal como lo pide el cheat-sheet de Clean Code del curso. Cada mensaje
# responde a las 4 preguntas que exige el cheat-sheet: qué pasó, por qué
# pasó, dónde pasó (el valor recibido) y cómo se soluciona.
# ---------------------------------------------------------------------------


class ErrorCalculoPension(Exception):
    """Excepción base de todas las reglas de negocio de la calculadora."""


class SemanasInsuficientes(ErrorCalculoPension):
    """Las semanas cotizadas son menores a las mínimas necesarias."""

    def __init__(self, semanas_cotizadas: int = None):
        detalle = (
            f" Usted ingresó {semanas_cotizadas} semanas."
            if semanas_cotizadas is not None
            else ""
        )
        super().__init__(
            "Semanas cotizadas insuficientes: el Régimen de Prima Media "
            f"exige mínimo {SEMANAS_MINIMAS} semanas cotizadas.{detalle} "
            "Solución: verifique la historia laboral e ingrese un valor "
            f"igual o mayor a {SEMANAS_MINIMAS}."
        )
        self.semanas_cotizadas = semanas_cotizadas


class SemanasNegativas(ErrorCalculoPension):
    """Las semanas cotizadas son negativas."""

    def __init__(self, semanas_cotizadas: int = None):
        detalle = f" (recibido: {semanas_cotizadas})" if semanas_cotizadas is not None else ""
        super().__init__(
            f"Las semanas cotizadas no pueden ser negativas{detalle}. "
            "Solución: ingrese un número de semanas mayor o igual a cero."
        )
        self.semanas_cotizadas = semanas_cotizadas


class IblCero(ErrorCalculoPension):
    """El IBL es cero."""

    def __init__(self):
        super().__init__(
            "El ingreso base de liquidación (IBL) es cero. "
            "Esto ocurre cuando el IBC de los últimos 10 años y el IBC de "
            "toda la vida laboral son ambos cero. "
            "Solución: ingrese un ingreso base de cotización mayor que cero."
        )


class IblNegativo(ErrorCalculoPension):
    """El IBL es negativo."""

    def __init__(self, ibl: float = None):
        detalle = f" (IBL calculado: {ibl})" if ibl is not None else ""
        super().__init__(
            f"El ingreso base de liquidación (IBL) no puede ser negativo{detalle}. "
            "Solución: verifique los valores de IBC ingresados."
        )
        self.ibl = ibl


class SalarioMinimoLegalVigenteCero(ErrorCalculoPension):
    """El salario mínimo legal vigente es cero."""

    def __init__(self):
        super().__init__(
            "El salario mínimo legal vigente no puede ser cero. "
            "Solución: ingrese el valor vigente del SMLMV (mayor que cero)."
        )


class SalarioMinimoNegativo(ErrorCalculoPension):
    """El salario mínimo legal vigente es negativo."""

    def __init__(self, salario_minimo_legal: int = None):
        detalle = (
            f" (recibido: {salario_minimo_legal})"
            if salario_minimo_legal is not None
            else ""
        )
        super().__init__(
            f"El salario mínimo legal no puede ser negativo{detalle}. "
            "Solución: ingrese el valor vigente del SMLMV, siempre positivo."
        )
        self.salario_minimo_legal = salario_minimo_legal


class EdadInsuficiente(ErrorCalculoPension):
    """La edad es insuficiente para acceder a la pensión."""

    def __init__(self, edad: int = None, sexo: str = None):
        detalle = f" Usted ingresó {edad} años ({sexo})." if edad is not None else ""
        super().__init__(
            "La edad es menor a la requerida para acceder a la pensión: "
            f"{EDAD_MINIMA_MUJER} años para mujeres o {EDAD_MINIMA_HOMBRE} "
            f"años para hombres.{detalle} "
            "Solución: la persona debe cumplir la edad mínima según su sexo."
        )
        self.edad = edad
        self.sexo = sexo


class SexoInvalido(ErrorCalculoPension):
    """El sexo ingresado no es válido."""

    def __init__(self, sexo: str = None):
        detalle = f" (recibido: '{sexo}')" if sexo is not None else ""
        super().__init__(
            f"El sexo debe ser 'M' (hombre) o 'F' (mujer){detalle}. "
            "Solución: ingrese únicamente 'M' o 'F'."
        )
        self.sexo = sexo


# ---------------------------------------------------------------------------
# Cálculos (cada función hace una sola cosa, con nombres y tipos explícitos).
# ---------------------------------------------------------------------------


def calcular_ibl(ibc_ultimos_10: float, ibc_toda_vida: float) -> float:
    """Retorna el ingreso base de liquidación (el IBC más favorable).

    La ley permite liquidar la pensión con el IBC que resulte más alto
    entre los últimos 10 años y toda la vida laboral; por eso se usa
    max() en vez de, por ejemplo, un promedio.
    """
    return max(ibc_ultimos_10, ibc_toda_vida)


def calcular_relacion_ibl_smlmv(
    ingreso_base_liquidacion: float, salario_minimo_legal: int
) -> float:
    """Retorna cuántos salarios mínimos representa el IBL.

    Este valor (a veces llamado "S" en la fórmula legal) es el insumo
    para calcular_r_base_55: mientras más salarios mínimos gane la
    persona, menor es su tasa de reemplazo base.
    """
    return ingreso_base_liquidacion / salario_minimo_legal


def calcular_r_base_55(relacion_ibl_smlmv: float) -> float:
    """Calcula la tasa base de reemplazo con piso del 55%.

    Parte de un 65,5% (TASA_REEMPLAZO_INICIAL) y le resta medio punto
    porcentual por cada salario mínimo que representa el IBL, sin
    bajar nunca del piso legal del 55%.
    """
    tasa = TASA_REEMPLAZO_INICIAL - relacion_ibl_smlmv * FACTOR_REDUCCION_POR_SALARIO
    return max(tasa, TASA_REEMPLAZO_MINIMA)


def calcular_semanas_adicionales(semanas_cotizadas: int) -> int:
    """Retorna las semanas cotizadas por encima de las mínimas.

    Solo las semanas que superan SEMANAS_MINIMAS (1300) cuentan como
    "adicionales" y son las que pueden generar incremento en la tasa.
    """
    return max(semanas_cotizadas - SEMANAS_MINIMAS, 0)


def calcular_incremento_porcentual(semanas_adicionales: int) -> float:
    """1.5 puntos porcentuales por cada bloque completo de 50 semanas.

    Se usa división entera (bloques_completos) a propósito: un bloque
    incompleto (por ejemplo 30 semanas adicionales de un bloque de 50)
    no genera ningún incremento, tal como lo exige la regla de negocio.
    """
    bloques_completos = int(semanas_adicionales / SEMANAS_POR_INCREMENTO)
    return bloques_completos * INCREMENTO_PORCENTUAL


def calcular_r_total(tasa_reemplazo_base: float, incremento: float) -> float:
    """Tasa total de reemplazo con tope máximo del 80%."""
    return min(tasa_reemplazo_base + incremento, TASA_REEMPLAZO_MAXIMA)


def cumple_requisitos(semanas_cotizadas: int, edad: int, sexo: str) -> bool:
    """Verifica si la persona cumple derecho a pensión de vejez.

    Ambos requisitos (semanas mínimas Y edad mínima según el sexo) se
    deben cumplir simultáneamente; no basta con cumplir solo uno.
    """
    tiene_semanas_minimas = semanas_cotizadas >= SEMANAS_MINIMAS
    tiene_edad_minima = (sexo == "F" and edad >= EDAD_MINIMA_MUJER) or (
        sexo == "M" and edad >= EDAD_MINIMA_HOMBRE
    )
    return tiene_semanas_minimas and tiene_edad_minima


# ---------------------------------------------------------------------------
# Validaciones: cada una encapsula la detección de UN solo error, tal como
# lo pide el cheat-sheet ("no mezcles el manejo de errores con el código").
# ---------------------------------------------------------------------------


def validar_ibl(datos: DatosPension) -> None:
    """Verifica que el IBL calculado no sea negativo ni cero."""
    ibl = calcular_ibl(datos.ibc_ultimos_10, datos.ibc_toda_vida)

    if ibl < 0:
        raise IblNegativo(ibl=ibl)

    if ibl == 0:
        raise IblCero()


def validar_salario_minimo(datos: DatosPension) -> None:
    """Verifica que el salario mínimo legal vigente sea mayor que cero."""
    if datos.salario_minimo_legal == 0:
        raise SalarioMinimoLegalVigenteCero()

    if datos.salario_minimo_legal < 0:
        raise SalarioMinimoNegativo(salario_minimo_legal=datos.salario_minimo_legal)


def validar_semanas(datos: DatosPension) -> None:
    """Verifica que las semanas cotizadas sean válidas y suficientes."""
    if datos.semanas_cotizadas < 0:
        raise SemanasNegativas(semanas_cotizadas=datos.semanas_cotizadas)

    if datos.semanas_cotizadas < SEMANAS_MINIMAS:
        raise SemanasInsuficientes(semanas_cotizadas=datos.semanas_cotizadas)


def validar_edad(datos: DatosPension) -> None:
    """Verifica que la edad cumpla el mínimo legal según el sexo."""
    if datos.sexo == "F" and datos.edad < EDAD_MINIMA_MUJER:
        raise EdadInsuficiente(edad=datos.edad, sexo=datos.sexo)

    if datos.sexo == "M" and datos.edad < EDAD_MINIMA_HOMBRE:
        raise EdadInsuficiente(edad=datos.edad, sexo=datos.sexo)


def validar_sexo(datos: DatosPension) -> None:
    """Verifica que el sexo sea uno de los dos valores permitidos."""
    if datos.sexo not in ("M", "F"):
        raise SexoInvalido(sexo=datos.sexo)


def validar_datos(datos: DatosPension) -> None:
    """Ejecuta, en orden, todas las validaciones de negocio.

    El orden importa para la experiencia del usuario: primero se
    valida el IBL y el salario mínimo (datos base del cálculo), luego
    semanas, edad y sexo (requisitos de elegibilidad), de modo que el
    primer error que vea el usuario sea siempre el más relevante.
    """
    validar_ibl(datos)
    validar_salario_minimo(datos)
    validar_semanas(datos)
    validar_edad(datos)
    validar_sexo(datos)


def calcular_pension(datos: DatosPension) -> ResultadoPension:
    """Calcula la pensión estimada de vejez (Régimen de Prima Media).

    Orquesta, en orden, los pasos descritos en el README del proyecto:
    1. Validar los datos de entrada.
    2. Calcular el IBL (el IBC más favorable).
    3. Calcular cuántos salarios mínimos representa ese IBL.
    4. Calcular la tasa de reemplazo base (piso 55%).
    5. Calcular semanas adicionales y su incremento en la tasa.
    6. Calcular la tasa total (techo 80%) y la pensión final,
       garantizando que nunca sea inferior a un salario mínimo.
    """
    validar_datos(datos)

    ingreso_base_liquidacion = calcular_ibl(
        ibc_ultimos_10=datos.ibc_ultimos_10, ibc_toda_vida=datos.ibc_toda_vida
    )

    relacion_ibl_smlmv = calcular_relacion_ibl_smlmv(
        ingreso_base_liquidacion=ingreso_base_liquidacion,
        salario_minimo_legal=datos.salario_minimo_legal,
    )

    tasa_reemplazo_base = calcular_r_base_55(relacion_ibl_smlmv=relacion_ibl_smlmv)

    semanas_adicionales = calcular_semanas_adicionales(
        semanas_cotizadas=datos.semanas_cotizadas
    )

    incremento = calcular_incremento_porcentual(semanas_adicionales=semanas_adicionales)

    tasa_reemplazo_total = calcular_r_total(
        tasa_reemplazo_base=tasa_reemplazo_base, incremento=incremento
    )

    # Garantía de pensión mínima: nunca puede ser inferior a un SMLMV.
    pension = round(
        max(
            ingreso_base_liquidacion * tasa_reemplazo_total / 100,
            datos.salario_minimo_legal,
        ),
        2,
    )

    return ResultadoPension(
        ibl=ingreso_base_liquidacion,
        relacion=relacion_ibl_smlmv,
        tasa_base=tasa_reemplazo_base,
        semanas_adicionales=semanas_adicionales,
        incremento=incremento,
        tasa_total=tasa_reemplazo_total,
        pension=pension,
    )