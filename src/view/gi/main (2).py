"""Interfaz gráfica (GUI) de la calculadora pensional con Kivy.

Uso:
    python src/view/gui/main.py

La vista delega toda la lógica en el controlador, que a su vez
delega en el modelo. No se realiza ningún cálculo aquí.
"""

import sys
import os

# Permite ejecutar el archivo directamente sin configurar Sources Root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock

from controller.pension_controller import (
    CalculadoraPensionController,
    MENSAJE_ENTRADA_INVALIDA,
)

# Paleta de colores de la aplicación
COLOR_PRIMARIO = (0.09, 0.45, 0.27, 1)    # verde institucional
COLOR_ERROR = (0.80, 0.20, 0.20, 1)
COLOR_FONDO = (0.95, 0.96, 0.97, 1)
COLOR_TEXTO = (0.12, 0.14, 0.16, 1)
COLOR_RESULTADO = (0.07, 0.36, 0.22, 1)


def formatear_miles(valor):
    """Formatea un número con separadores de miles tipo 1.234.567,89."""
    entero, _, decimal = f"{valor:,.2f}".partition(".")
    entero = entero.replace(",", ".")
    return f"{entero},{decimal}"


class CalculadoraPensionApp(App):
    """Aplicación Kivy de la calculadora pensional."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.controlador = CalculadoraPensionController()
        self._ultimo_resultado = None

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def build(self):
        self.title = "Calculadora Pensional - Régimen de Prima Media"
        self.icon = ""  # sin ícono empaquetado; Kivy usa el predeterminado

        raiz = BoxLayout(orientation="vertical", padding=12, spacing=10)
        raiz.add_widget(self._crear_encabezado())
        raiz.add_widget(self._crear_formulario())
        raiz.add_widget(self._crear_botones())
        raiz.add_widget(self._crear_panel_resultados())
        return raiz

    def _crear_encabezado(self):
        encabezado = Label(
            text="CALCULADORA PENSIONAL\nRégimen de Prima Media - Colombia",
            size_hint_y=None,
            height=70,
            bold=True,
            font_size="20sp",
            color=COLOR_PRIMARIO,
        )
        return encabezado

    def _crear_formulario(self):
        """Crea la rejilla de campos de entrada con etiquetas."""
        formulario = GridLayout(cols=2, spacing=10, size_hint_y=None)
        formulario.bind(minimum_height=formulario.setter("height"))

        self.campos = {}

        campos_definicion = [
            ("ibc_ultimos_10", "IBC últimos 10 años ($):", "ej. 9800000"),
            ("ibc_toda_vida", "IBC toda la vida laboral ($):", "ej. 10000000"),
            ("salario_minimo", "Salario mínimo legal vigente ($):", "ej. 1423500"),
            ("semanas", "Semanas cotizadas:", "ej. 1300"),
            ("edad", "Edad:", "ej. 62"),
        ]

        for clave, etiqueta, ayuda in campos_definicion:
            formulario.add_widget(self._crear_etiqueta(etiqueta))
            self.campos[clave] = self._crear_entrada(ayuda)
            formulario.add_widget(self.campos[clave])

        formulario.add_widget(self._crear_etiqueta("Sexo:"))
        self.spinner_sexo = Spinner(
            text="Seleccione...",
            values=("M - Hombre", "F - Mujer"),
            size_hint_y=None,
            height=44,
            background_color=COLOR_PRIMARIO,
        )
        formulario.add_widget(self.spinner_sexo)

        contenedor = ScrollView(size_hint=(1, 1))
        contenedor.add_widget(formulario)
        return contenedor

    def _crear_etiqueta(self, texto):
        return Label(
            text=texto,
            size_hint_y=None,
            height=44,
            color=COLOR_TEXTO,
            halign="left",
            valign="middle",
        )

    def _crear_entrada(self, ayuda):
        entrada = TextInput(
            hint_text=ayuda,
            multiline=False,
            size_hint_y=None,
            height=44,
            input_filter="float",
            background_color=(1, 1, 1, 1),
            foreground_color=COLOR_TEXTO,
        )
        return entrada

    def _crear_botones(self):
        fila = BoxLayout(size_hint_y=None, height=52, spacing=10)

        boton_calcular = Button(
            text="CALCULAR PENSIÓN",
            background_color=COLOR_PRIMARIO,
            bold=True,
        )
        boton_calcular.bind(on_release=lambda *_: self.calcular())

        boton_limpiar = Button(
            text="LIMPIAR",
            background_color=(0.45, 0.47, 0.50, 1),
        )
        boton_limpiar.bind(on_release=lambda *_: self.limpiar())

        fila.add_widget(boton_calcular)
        fila.add_widget(boton_limpiar)
        return fila

    def _crear_panel_resultados(self):
        self.panel_resultados = Label(
            text="Complete los datos y presione CALCULAR PENSIÓN.",
            size_hint_y=None,
            height=260,
            valign="top",
            color=COLOR_TEXTO,
            background_color=COLOR_FONDO,
        )
        self.panel_resultados.bind(size=self.panel_resultados.setter("text_size"))
        contenedor = ScrollView(size_hint_y=None, height=280)
        contenedor.add_widget(self.panel_resultados)
        return contenedor

    # ------------------------------------------------------------------
    # Acciones del usuario
    # ------------------------------------------------------------------
    def calcular(self):
        """Lee los campos, delega en el controlador y muestra resultados."""
        try:
            datos = self._leer_datos()
        except ValueError:
            self._mostrar_error(MENSAJE_ENTRADA_INVALIDA)
            return

        try:
            resultado = self.controlador.calcular(datos)
        except Exception as error:
            self._mostrar_error(self.controlador.mensaje_de_error(error))
            return

        self._ultimo_resultado = resultado
        self._mostrar_resultados(resultado)

    def limpiar(self):
        """Restablece todos los campos y el panel de resultados."""
        for campo in self.campos.values():
            campo.text = ""
        self.spinner_sexo.text = "Seleccione..."
        self._ultimo_resultado = None
        self.panel_resultados.text = (
            "Complete los datos y presione CALCULAR PENSIÓN."
        )
        self.panel_resultados.color = COLOR_TEXTO

    # ------------------------------------------------------------------
    # Lectura y validación de entradas
    # ------------------------------------------------------------------
    def _leer_datos(self):
        """Convierte el texto de los campos a datos del modelo."""
        ibc_10 = float(self.campos["ibc_ultimos_10"].text or 0)
        ibc_vida = float(self.campos["ibc_toda_vida"].text or 0)
        salario = float(self.campos["salario_minimo"].text or 0)
        semanas = float(self.campos["semanas"].text or 0)
        edad = float(self.campos["edad"].text or 0)
        sexo = self._leer_sexo()

        return self.controlador.construir_datos(
            ibc_ultimos_10=ibc_10,
            ibc_toda_vida=ibc_vida,
            salario_minimo_legal=int(salario),
            semanas_cotizadas=int(semanas),
            edad=int(edad),
            sexo=sexo,
        )

    def _leer_sexo(self):
        texto = self.spinner_sexo.text
        if texto.startswith("M"):
            return "M"
        if texto.startswith("F"):
            return "F"
        raise ValueError("Sexo no seleccionado")

    # ------------------------------------------------------------------
    # Presentación de resultados y errores
    # ------------------------------------------------------------------
    def _mostrar_resultados(self, resultado):
        lineas = self.controlador.formatear_resultado(resultado)
        # Reemplazar los números grandes con formato local de miles
        lineas = [
            l.replace(f"${resultado.ibl:,.2f}", f"${formatear_miles(resultado.ibl)}")
             .replace(f"${resultado.pension:,.2f}", f"${formatear_miles(resultado.pension)}")
            for l in lineas
        ]

        texto = "\n".join(lineas)
        self.panel_resultados.text = texto
        self.panel_resultados.color = COLOR_RESULTADO
        self.panel_resultados.bold = True

        # Resaltar visualmente la pensión estimada
        Clock.schedule_once(lambda dt: self._resaltar_pension(), 0.1)

    def _resaltar_pension(self):
        if self._ultimo_resultado:
            self.panel_resultados.font_size = "16sp"

    def _mostrar_error(self, mensaje):
        """Muestra un popup amigable con el mensaje de error."""
        contenido = BoxLayout(orientation="vertical", padding=10, spacing=10)
        contenido.add_widget(Label(
            text=mensaje,
            color=COLOR_TEXTO,
            text_size=(300, None),
        ))
        boton_cerrar = Button(text="Entendido", size_hint_y=None, height=44)
        contenido.add_widget(boton_cerrar)

        popup = Popup(
            title="Error de validación",
            content=contenido,
            size_hint=(None, None),
            size=(360, 220),
            auto_dismiss=True,
        )
        boton_cerrar.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    CalculadoraPensionApp().run()
