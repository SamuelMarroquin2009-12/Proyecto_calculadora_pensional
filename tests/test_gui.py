"""Pruebas de la capa GUI (Kivy).

No duplican lógica de negocio: construyen la app real con ``build()``
(headless, sin mostrar ventana) y ejercitan los métodos de la vista que
antes solo se podían probar manualmente -- lectura/validación de campos,
el simulador de semanas adicionales y el guardado en archivo -- delegando
siempre en el controlador y el modelo reales.
"""

import os
import sys
import shutil
import tempfile
import unittest
from unittest.mock import PropertyMock, patch

sys.path.append("src")

os.environ.setdefault("KIVY_NO_ARGS", "1")

try:
    from view.gui.main import CalculadoraPensionApp, MENSAJE_ENTRADA_INVALIDA
    from model.logica_pension import ErrorCalculoPension
    _ERROR_IMPORTACION_KIVY = None
except Exception as error:  # pragma: no cover - depende del entorno gráfico
    # Kivy necesita una ventana/GL real para construir widgets. Si el
    # entorno no la tiene (por ejemplo, un CI sin pantalla), estas pruebas
    # se omiten en vez de romper el resto de la suite (tests/test_pension.py
    # y tests/test_controller.py, que no dependen de Kivy).
    _ERROR_IMPORTACION_KIVY = error


def _construir_app() -> CalculadoraPensionApp:
    """Crea y construye (headless) una instancia real de la app.

    Si Kivy no está instalado o el entorno no tiene una ventana/GL
    disponible, omite la prueba en lugar de fallar.
    """
    if _ERROR_IMPORTACION_KIVY is not None:
        raise unittest.SkipTest(
            f"Kivy no disponible en este entorno: {_ERROR_IMPORTACION_KIVY}"
        )
    try:
        app = CalculadoraPensionApp()
        app.build()
    except Exception as error:
        raise unittest.SkipTest(f"No se pudo construir la GUI (sin pantalla): {error}")
    return app


def _llenar_formulario_valido(app: CalculadoraPensionApp) -> None:
    app.campos["ibc_ultimos_10"].text = "9800000"
    app.campos["ibc_toda_vida"].text = "10000000"
    app.campos["salario_minimo"].text = "2000000"
    app.campos["semanas"].text = "1300"
    app.campos["edad"].text = "65"
    app.spinner_sexo.text = "M - Hombre"


class TestValidacionCamposEnteros(unittest.TestCase):
    """El campo de semanas y el de edad deben exigir números enteros,
    igual que ya lo hace la vista de consola (``solicitar_entero``)."""

    def setUp(self):
        self.app = _construir_app()

    def test_semanas_entero_valido_se_acepta(self):
        self.app.campos["semanas"].text = "1300"
        self.assertEqual(self.app._leer_campo_entero(clave="semanas"), 1300)

    def test_semanas_con_decimal_se_rechaza(self):
        self.app.campos["semanas"].text = "1300.9"
        with self.assertRaises(ValueError):
            self.app._leer_campo_entero(clave="semanas")

    def test_edad_con_decimal_se_rechaza(self):
        self.app.campos["edad"].text = "62.9"
        with self.assertRaises(ValueError):
            self.app._leer_campo_entero(clave="edad")

    def test_edad_como_flotante_sin_parte_decimal_se_acepta(self):
        self.app.campos["edad"].text = "62.0"
        self.assertEqual(self.app._leer_campo_entero(clave="edad"), 62)

    def test_campo_vacio_reporta_mensaje_de_entrada_invalida(self):
        self.app.campos["semanas"].text = ""
        with self.assertRaises(ValueError) as contexto:
            self.app._leer_campo_entero(clave="semanas")
        self.assertIn(MENSAJE_ENTRADA_INVALIDA, str(contexto.exception))

    def test_leer_datos_formulario_completo_construye_datos_pension(self):
        _llenar_formulario_valido(self.app)
        datos = self.app._leer_datos_formulario()
        self.assertEqual(datos.semanas_cotizadas, 1300)
        self.assertEqual(datos.edad, 65)
        self.assertEqual(datos.sexo, "M")
        self.assertIsInstance(datos.salario_minimo_legal, int)


class TestSimuladorSemanasAdicionales(unittest.TestCase):
    """Funcionalidad extra 1: simular más semanas cotizadas sin alterar
    los datos originales del último cálculo."""

    def setUp(self):
        self.app = _construir_app()
        _llenar_formulario_valido(self.app)
        self.app.calcular()

    def test_calculo_inicial_habilita_el_simulador(self):
        self.assertFalse(self.app.slider_semanas_extra.disabled)
        self.assertFalse(self.app.boton_guardar.disabled)

    def test_simular_no_modifica_las_semanas_originales(self):
        semanas_originales = self.app._ultimos_datos.semanas_cotizadas
        self.app._actualizar_texto_simulador(semanas_extra=100)
        self.assertEqual(self.app._ultimos_datos.semanas_cotizadas, semanas_originales)
        self.assertEqual(self.app.campos["semanas"].text, "1300")

    def test_simular_usa_el_controlador_y_muestra_la_pension_recalculada(self):
        self.app._actualizar_texto_simulador(semanas_extra=100)
        self.assertIn("100", self.app.etiqueta_simulador.text)
        self.assertIn("pensión estimada", self.app.etiqueta_simulador.text.lower())

    def test_simular_con_datos_invalidos_no_rompe_la_gui(self):
        # Sexo inválido a propósito para forzar ErrorCalculoPension dentro
        # del simulador; no debe propagar la excepción hacia la GUI.
        self.app._ultimos_datos.sexo = "X"
        try:
            self.app._actualizar_texto_simulador(semanas_extra=50)
        except ErrorCalculoPension:
            self.fail("El simulador no debe propagar ErrorCalculoPension a la GUI")

    def test_limpiar_deshabilita_el_simulador(self):
        self.app.limpiar()
        self.assertTrue(self.app.slider_semanas_extra.disabled)
        self.assertTrue(self.app.boton_guardar.disabled)
        self.assertIsNone(self.app._ultimos_datos)


class TestGuardarResultadoEnArchivo(unittest.TestCase):
    """Funcionalidad extra 2: guardar el último resultado en un archivo
    dentro de ``user_data_dir`` (nunca una ruta fija del proyecto)."""

    def setUp(self):
        self.directorio_temporal = tempfile.mkdtemp()
        self.app = _construir_app()
        _llenar_formulario_valido(self.app)
        self.app.calcular()

    def tearDown(self):
        shutil.rmtree(self.directorio_temporal, ignore_errors=True)

    def test_guardar_sin_calculo_previo_muestra_error_y_no_crea_archivo(self):
        app_sin_calculo = _construir_app()
        with patch.object(
            type(app_sin_calculo),
            "user_data_dir",
            new_callable=PropertyMock,
            return_value=self.directorio_temporal,
        ):
            app_sin_calculo.guardar_resultado()
        self.assertEqual(os.listdir(self.directorio_temporal), [])

    def test_guardar_resultado_crea_archivo_en_user_data_dir(self):
        with patch.object(
            type(self.app),
            "user_data_dir",
            new_callable=PropertyMock,
            return_value=self.directorio_temporal,
        ):
            self.app.guardar_resultado()
            ruta_esperada = os.path.join(
                self.directorio_temporal, "resultado_pension.txt"
            )
            self.assertTrue(os.path.isfile(ruta_esperada))
            with open(ruta_esperada, encoding="utf-8") as archivo:
                contenido = archivo.read()
            self.assertIn("PENSIÓN ESTIMADA", contenido)

    def test_guardar_resultado_dos_veces_agrega_en_vez_de_sobrescribir(self):
        with patch.object(
            type(self.app),
            "user_data_dir",
            new_callable=PropertyMock,
            return_value=self.directorio_temporal,
        ):
            self.app.guardar_resultado()
            self.app.guardar_resultado()
            ruta = os.path.join(self.directorio_temporal, "resultado_pension.txt")
            with open(ruta, encoding="utf-8") as archivo:
                contenido = archivo.read()
            self.assertEqual(contenido.count("PENSIÓN ESTIMADA"), 2)

    def test_guardar_resultado_maneja_error_de_escritura_sin_romper_la_app(self):
        with patch.object(
            type(self.app),
            "user_data_dir",
            new_callable=PropertyMock,
            return_value=self.directorio_temporal,
        ), patch("builtins.open", side_effect=OSError("disco lleno")):
            try:
                self.app.guardar_resultado()
            except OSError:
                self.fail(
                    "guardar_resultado() debe capturar OSError y mostrar "
                    "un mensaje amigable, no propagar la excepción"
                )


if __name__ == "__main__":
    unittest.main()
