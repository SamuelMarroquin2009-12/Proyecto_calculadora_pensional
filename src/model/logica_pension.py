"""Lógica de negocio de la calculadora pensional.

Régimen de Prima Media - Pensión de Vejez en Colombia.

Este módulo contiene toda la lógica de cálculo y validación.
Es compartido por la interfaz de consola y la interfaz gráfica (Kivy),
por lo que no debe depender de ninguna librería de interfaz.
"""

from dataclasses import dataclass


SEMANAS_MINIMAS = 1300
SEMANAS_POR_INCREMENTO = 50
INCREMENTO_PORCENTUAL = 1.5

TASA_REEMPLAZO_INICIAL = 65.5
FACTOR_REDUCCION_POR_SALARIO = 0.5
TASA_REEMPLAZO_MINIMA = 55
TASA_REEMPLAZO_MAXIMA = 80

EDAD_MINIMA_MUJER = 57
EDAD_MINIMA_HOMBRE = 62


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


class SemanasInsuficientes(Exception):
    """Las semanas cotizadas son menores a las mínimas necesarias."""

    def __init__(self):
        super().__init__("Las semanas cotizadas son menores a las mínimas necesarias")


class IblCero(Exception):
    """El IBL es cero."""

    def __init__(self):
        super().__init__("El IBL no puede ser cero")


class SalarioMinimoLegalVigenteCero(Exception):
    """El salario mínimo legal vigente es cero."""

    def __init__(self):
        super().__init__("El salario mínimo legal vigente no puede ser cero")


class SalarioMinimoNegativo(Exception):
    """El salario mínimo legal vigente es negativo."""

    def __init__(self):
        super().__init__("El salario mínimo legal no puede ser negativo")


class SemanasNegativas(Exception):
    """Las semanas cotizadas son negativas."""

    def __init__(self):
        super().__init__("Las semanas cotizadas no pueden ser negativas")


class IblNegativo(Exception):
    """El IBL es negativo."""

    def __init__(self):
        super().__init__("El IBL no puede ser negativo")


class EdadInsuficiente(Exception):
    """La edad es insuficiente para acceder a la pensión."""

    def __init__(self):
        super().__init__("La edad es menor a la requerida para acceder a la pensión")


class SexoInvalido(Exception):
    """El sexo ingresado no es válido."""

    def __init__(self):
        super().__init__("El sexo debe ser 'M' (hombre) o 'F' (mujer)")


def calcular_ibl(ibc_ultimos_10: float, ibc_toda_vida: float) -> float:
    """Retorna el ingreso base de liquidación (el IBC más favorable)."""
    return max(ibc_ultimos_10, ibc_toda_vida)


def calcular_relacion_ibl_smlmv(ingreso_base_liquidacion: float,
                                salario_minimo_legal: int) -> float:
    """Retorna cuántos salarios mínimos representa el IBL."""
    return ingreso_base_liquidacion / salario_minimo_legal


def calcular_r_base_55(relacion_ibl_smlmv: float) -> float:
    """Calcula la tasa base de reemplazo con piso del 55%."""
    tasa = TASA_REEMPLAZO_INICIAL - relacion_ibl_smlmv * FACTOR_REDUCCION_POR_SALARIO
    return max(tasa, TASA_REEMPLAZO_MINIMA)


def semanas_adicionales_test(semanas_cotizadas: int) -> int:
    """Retorna las semanas cotizadas por encima de las 1300 mínimas."""
    return max(semanas_cotizadas - SEMANAS_MINIMAS, 0)


def incremento_porcentual(semanas_adicionales: int) -> float:
    """1.5 puntos porcentuales por cada bloque completo de 50 semanas."""
    return int(semanas_adicionales / SEMANAS_POR_INCREMENTO) * INCREMENTO_PORCENTUAL


def calcular_r_total(tasa_reemplazo_base: float, incremento: float) -> float:
    """Tasa total de reemplazo con tope máximo del 80%."""
    return min(tasa_reemplazo_base + incremento, TASA_REEMPLAZO_MAXIMA)


def cumple_requisitos(semanas_cotizadas: int, edad: int, sexo: str) -> bool:
    """Verifica si la persona cumple derecho a pensión de vejez."""
    return (
        semanas_cotizadas >= SEMANAS_MINIMAS
        and (
            (sexo == "F" and edad >= EDAD_MINIMA_MUJER)
            or (sexo == "M" and edad >= EDAD_MINIMA_HOMBRE)
        )
    )


def validar_ibl(datos: DatosPension):
    ibl = calcular_ibl(datos.ibc_ultimos_10, datos.ibc_toda_vida)

    if ibl < 0:
        raise IblNegativo()

    if ibl == 0:
        raise IblCero()


def validar_salario_minimo(datos: DatosPension):
    if datos.salario_minimo_legal == 0:
        raise SalarioMinimoLegalVigenteCero()

    if datos.salario_minimo_legal < 0:
        raise SalarioMinimoNegativo()


def validar_semanas(datos: DatosPension):
    if datos.semanas_cotizadas < 0:
        raise SemanasNegativas()

    if datos.semanas_cotizadas < SEMANAS_MINIMAS:
        raise SemanasInsuficientes()


def validar_edad(datos: DatosPension):
    if datos.sexo == "F" and datos.edad < EDAD_MINIMA_MUJER:
        raise EdadInsuficiente()

    if datos.sexo == "M" and datos.edad < EDAD_MINIMA_HOMBRE:
        raise EdadInsuficiente()


def validar_sexo(datos: DatosPension):
    if datos.sexo not in ("M", "F"):
        raise SexoInvalido()


def validar_datos(datos: DatosPension):
    validar_ibl(datos)
    validar_salario_minimo(datos)
    validar_semanas(datos)
    validar_edad(datos)
    validar_sexo(datos)


def calcular_pension(datos: DatosPension) -> ResultadoPension:
    """Calcula la pensión estimada de vejez (Régimen de Prima Media)."""
    validar_datos(datos)

    ingreso_base_liquidacion = calcular_ibl(
        datos.ibc_ultimos_10, datos.ibc_toda_vida
    )

    relacion_ibl_smlmv = calcular_relacion_ibl_smlmv(
        ingreso_base_liquidacion, datos.salario_minimo_legal
    )

    tasa_reemplazo_base = calcular_r_base_55(relacion_ibl_smlmv)

    semanas_adicionales = semanas_adicionales_test(datos.semanas_cotizadas)

    incremento = incremento_porcentual(semanas_adicionales)

    tasa_reemplazo_total = calcular_r_total(tasa_reemplazo_base, incremento)

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
