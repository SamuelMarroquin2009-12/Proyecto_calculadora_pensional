import sys
import unittest

sys.path.append("src")

from controller.pension_controller import (
    CalculadoraPensionController,
    MENSAJE_ENTRADA_INVALIDA,
)
from model import logica_pension


class TestController(unittest.TestCase):

    def setUp(self):
        self.controlador = CalculadoraPensionController()

    def test_calcular_delega_en_el_modelo(self):
        datos = self.controlador.construir_datos(
            ibc_ultimos_10=9_800_000,
            ibc_toda_vida=10_000_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1300,
            edad=65,
            sexo="M",
        )

        resultado = self.controlador.calcular(datos)

        self.assertIsInstance(resultado, logica_pension.ResultadoPension)
        self.assertAlmostEqual(resultado.pension, 6_300_000.00, 2)

    def test_construir_datos_normaliza_el_sexo(self):
        datos = self.controlador.construir_datos(
            ibc_ultimos_10=1,
            ibc_toda_vida=1,
            salario_minimo_legal=1_000_000,
            semanas_cotizadas=1300,
            edad=65,
            sexo="  m ",
        )

        self.assertEqual(datos.sexo, "M")

    def test_mensaje_de_error_semanas_insuficientes(self):
        error = logica_pension.SemanasInsuficientes()
        mensaje = self.controlador.mensaje_de_error(error)

        self.assertIn("1300", mensaje)

    def test_mensaje_de_error_edad_insuficiente(self):
        error = logica_pension.EdadInsuficiente()
        mensaje = self.controlador.mensaje_de_error(error)

        self.assertIn("57", mensaje)
        self.assertIn("62", mensaje)

    def test_mensaje_de_error_desconocido(self):
        mensaje = self.controlador.mensaje_de_error(RuntimeError("falla"))

        self.assertIn("inesperado", mensaje)

    def test_mensaje_entrada_invalida_existe(self):
        self.assertTrue(len(MENSAJE_ENTRADA_INVALIDA) > 0)

    def test_formatear_resultado_contiene_pension(self):
        datos = self.controlador.construir_datos(
            ibc_ultimos_10=9_800_000,
            ibc_toda_vida=10_000_000,
            salario_minimo_legal=2_000_000,
            semanas_cotizadas=1300,
            edad=65,
            sexo="M",
        )

        resultado = self.controlador.calcular(datos)
        lineas = self.controlador.formatear_resultado(resultado)

        self.assertTrue(any("PENSIÓN ESTIMADA" in l for l in lineas))
        self.assertEqual(len(lineas), 7)


if __name__ == "__main__":
    unittest.main()
