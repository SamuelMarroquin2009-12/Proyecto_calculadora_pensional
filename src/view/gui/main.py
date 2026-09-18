"""Interfaz gráfica (GUI) de la calculadora pensional con Kivy.

Uso:
    python src/view/gui/main.py
    (o, desde la raíz del repositorio: python main.py)

La vista delega toda la lógica en el controlador, que a su vez delega
en el modelo. No se realiza ningún cálculo de negocio aquí: esta capa
solo lee la entrada del usuario, la envía al controlador y presenta
el resultado o el error.
"""

import sys
import os
from dataclasses import replace
from datetime import datetime
from typing import Dict, Optional

# Permite ejecutar el archivo directamente sin configurar Sources Root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle

from controller.pension_controller import (
    CalculadoraPensionController,
    MENSAJE_ENTRADA_INVALIDA,
)
from model.logica_pension import DatosPension, ErrorCalculoPension, ResultadoPension


# ---------------------------------------------------------------------------
# Presentación (nada de esto es lógica de negocio).
# ---------------------------------------------------------------------------

COLOR_PRIMARIO = (0.09, 0.45, 0.27, 1)
COLOR_ERROR = (0.80, 0.20, 0.20, 1)
COLOR_FONDO = (0.95, 0.96, 0.97, 1)
COLOR_TEXTO = (0.12, 0.14, 0.16, 1)
COLOR_RESULTADO = (0.07, 0.36, 0.22, 1)

TEXTO_INICIAL_RESULTADOS = (
    "Complete los datos y presione CALCULAR PENSIÓN.\n"
    "Ayuda: los campos con $ aceptan solo números; use punto para "
    "decimales. Sexo debe ser 'M' u 'F'."
)

MAXIMO_SEMANAS_SIMULADAS = 500
NOMBRE_ARCHIVO_EXPORTADO = "resultado_pension.txt"

CAMPOS_DEFINICION = (
    ("ibc_ultimos_10", "IBC últimos 10 años ($):", "ej. 9800000"),
    ("ibc_toda_vida", "IBC toda la vida laboral ($):", "ej. 10000000"),
    ("salario_minimo", "Salario mínimo legal vigente ($):", "ej. 1423500"),
    ("semanas", "Semanas cotizadas:", "ej. 1300"),
    ("edad", "Edad:", "ej. 62"),
)


def formatear_miles(valor: float) -> str:
    """Formatea un número con separadores de miles tipo 1.234.567,89."""
    entero, _, decimal = f"{valor:,.2f}".partition(".")
    entero = entero.replace(",", ".")
    return f"{entero},{decimal}"


class CalculadoraPensionApp(App):
    """Aplicación Kivy de la calculadora pensional."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.controlador = CalculadoraPensionController()
        self.campos: Dict[str, TextInput] = {}
        self._ultimos_datos: Optional[DatosPension] = None
        self._ultimo_resultado: Optional[ResultadoPension] = None

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def build(self) -> BoxLayout:
        self.title = "Calculadora Pensional - Régimen de Prima Media"

        raiz = BoxLayout(orientation="vertical", padding=12, spacing=10)
        raiz.add_widget(self._crear_encabezado())
        raiz.add_widget(self._crear_formulario())
        raiz.add_widget(self._crear_botones())
        raiz.add_widget(self._crear_panel_resultados())
        raiz.add_widget(self._crear_panel_simulador())
        return raiz

    def _crear_encabezado(self) -> Label:
        # Responde "¿dónde estoy?": nombre de la app y del régimen.
        return Label(
            text="CALCULADORA PENSIONAL\nRégimen de Prima Media - Colombia",
            size_hint_y=None,
            height=70,
            bold=True,
            font_size="20sp",
            color=COLOR_PRIMARIO,
        )

    def _crear_formulario(self) -> ScrollView:
        """Crea la rejilla de campos de entrada con etiquetas."""
        formulario = GridLayout(cols=2, spacing=10, size_hint_y=None)
        formulario.bind(minimum_height=formulario.setter("height"))

        for clave, etiqueta, ayuda in CAMPOS_DEFINICION:
            formulario.add_widget(self._crear_etiqueta(texto=etiqueta))
            self.campos[clave] = self._crear_entrada(ayuda=ayuda)
            formulario.add_widget(self.campos[clave])

        formulario.add_widget(self._crear_etiqueta(texto="Sexo:"))
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

    def _crear_etiqueta(self, texto: str) -> Label:
        return Label(
            text=texto,
            size_hint_y=None,
            height=44,
            color=COLOR_TEXTO,
            halign="left",
            valign="middle",
        )

    def _crear_entrada(self, ayuda: str) -> TextInput:
        # El hint_text responde "¿qué se espera que haga aquí?".
        return TextInput(
            hint_text=ayuda,
            multiline=False,
            size_hint_y=None,
            height=44,
            input_filter="float",
            background_color=(1, 1, 1, 1),
            foreground_color=COLOR_TEXTO,
        )

    def _crear_botones(self) -> BoxLayout:
        fila = BoxLayout(size_hint_y=None, height=52, spacing=10)

        boton_calcular = Button(
            text="CALCULAR PENSIÓN", background_color=COLOR_PRIMARIO, bold=True
        )
        boton_calcular.bind(on_release=lambda _: self.calcular())

        boton_limpiar = Button(text="LIMPIAR", background_color=(0.45, 0.47, 0.50, 1))
        boton_limpiar.bind(on_release=lambda _: self.limpiar())

        self.boton_guardar = Button(
            text="GUARDAR EN ARCHIVO",
            background_color=(0.20, 0.33, 0.55, 1),
            disabled=True,
        )
        self.boton_guardar.bind(on_release=lambda _: self.guardar_resultado())

        fila.add_widget(boton_calcular)
        fila.add_widget(boton_limpiar)
        fila.add_widget(self.boton_guardar)
        return fila

    def _crear_panel_resultados(self) -> ScrollView:
        self.panel_resultados = Label(
            text=TEXTO_INICIAL_RESULTADOS,
            size_hint_y=None,
            height=220,
            valign="top",
            color=COLOR_TEXTO,
        )
        with self.panel_resultados.canvas.before:
            self._color_fondo_resultados = Color(*COLOR_FONDO)
            self._rect_fondo_resultados = Rectangle(
                pos=self.panel_resultados.pos, size=self.panel_resultados.size
            )
        self.panel_resultados.bind(
            pos=self._actualizar_fondo_resultados, size=self._actualizar_fondo_resultados
        )
        self.panel_resultados.bind(size=self.panel_resultados.setter("text_size"))
        contenedor = ScrollView(size_hint_y=None, height=230)
        contenedor.add_widget(self.panel_resultados)
        return contenedor

    def _crear_panel_simulador(self) -> BoxLayout:
        """Panel del simulador 'qué pasaría si cotizo más semanas'.

        Queda deshabilitado hasta que exista un cálculo exitoso, porque
        el simulador necesita los últimos datos válidos para funcionar.
        """
        panel = BoxLayout(orientation="vertical", size_hint_y=None, height=80, spacing=4)

        self.etiqueta_simulador = Label(
            text="Simulador: calcule una pensión primero para habilitarlo.",
            size_hint_y=None,
            height=30,
            color=COLOR_PRIMARIO,
            bold=True,
        )

        self.slider_semanas_extra = Slider(
            min=0,
            max=MAXIMO_SEMANAS_SIMULADAS,
            value=0,
            step=10,
            size_hint_y=None,
            height=30,
            disabled=True,
        )
        self.slider_semanas_extra.bind(value=self._simular_semanas_adicionales)

        panel.add_widget(self.etiqueta_simulador)
        panel.add_widget(self.slider_semanas_extra)
        return panel

    def _actualizar_fondo_resultados(self, *_args) -> None:
        """Mantiene el rectángulo de fondo alineado con el widget."""
        self._rect_fondo_resultados.pos = self.panel_resultados.pos
        self._rect_fondo_resultados.size = self.panel_resultados.size

    # ------------------------------------------------------------------
    # Acción principal: calcular (dividida en pasos pequeños)
    # ------------------------------------------------------------------
    def calcular(self) -> None:
        """Orquesta el cálculo: leer, calcular y mostrar el resultado."""
        try:
            datos = self._leer_datos_formulario()
        except ValueError as error:
            self._mostrar_error(mensaje=str(error))
            return

        try:
            resultado = self._ejecutar_calculo(datos=datos)
        except ErrorCalculoPension as error:
            self._mostrar_error(mensaje=self.controlador.mensaje_de_error(error))
            return
        except Exception as error:
            # Último recurso de resiliencia (requisito de la actividad):
            # ningún error de programación no previsto debe cerrar la app.
            self._mostrar_error(mensaje=self.controlador.mensaje_de_error(error))
            return

        self._guardar_ultimo_calculo(datos=datos, resultado=resultado)
        self._mostrar_resultados(resultado=resultado)
        self._habilitar_simulador()

    def _ejecutar_calculo(self, datos: DatosPension) -> ResultadoPension:
        """Delega el cálculo en el controlador (sin lógica propia)."""
        return self.controlador.calcular(datos=datos)

    def _guardar_ultimo_calculo(
        self, datos: DatosPension, resultado: ResultadoPension
    ) -> None:
        self._ultimos_datos = datos
        self._ultimo_resultado = resultado

    def limpiar(self) -> None:
        """Restablece todos los campos, el resultado y el simulador."""
        for campo in self.campos.values():
            campo.text = ""
        self.spinner_sexo.text = "Seleccione..."
        self._ultimos_datos = None
        self._ultimo_resultado = None
        self.panel_resultados.text = TEXTO_INICIAL_RESULTADOS
        self.panel_resultados.color = COLOR_TEXTO
        self._deshabilitar_simulador()
        self.boton_guardar.disabled = True

    # ------------------------------------------------------------------
    # Lectura y validación de formato de los campos (no son reglas de
    # negocio: son errores de formato, por eso lanzan ValueError, no
    # ErrorCalculoPension).
    # ------------------------------------------------------------------
    def _leer_datos_formulario(self) -> DatosPension:
        """Convierte el texto de los campos a un DatosPension."""
        ibc_10 = self._leer_campo_numerico(clave="ibc_ultimos_10")
        ibc_vida = self._leer_campo_numerico(clave="ibc_toda_vida")
        salario = self._leer_campo_numerico(clave="salario_minimo")
        semanas = self._leer_campo_numerico(clave="semanas")
        edad = self._leer_campo_numerico(clave="edad")
        sexo = self._leer_sexo()

        return self.controlador.construir_datos(
            ibc_ultimos_10=ibc_10,
            ibc_toda_vida=ibc_vida,
            salario_minimo_legal=int(salario),
            semanas_cotizadas=int(semanas),
            edad=int(edad),
            sexo=sexo,
        )

    def _leer_campo_numerico(self, clave: str) -> float:
        texto = self.campos[clave].text.strip()
        if not texto:
            raise ValueError(f"{MENSAJE_ENTRADA_INVALIDA}\nCampo vacío: '{clave}'.")
        try:
            return float(texto)
        except ValueError as error:
            raise ValueError(
                f"{MENSAJE_ENTRADA_INVALIDA}\nCampo inválido: '{clave}' = '{texto}'."
            ) from error

    def _leer_sexo(self) -> str:
        texto = self.spinner_sexo.text
        if texto.startswith("M"):
            return "M"
        if texto.startswith("F"):
            return "F"
        raise ValueError(
            "Debe seleccionar el sexo antes de calcular.\n"
            "Solución: use el desplegable 'Sexo' y elija 'M' o 'F'."
        )

    # ------------------------------------------------------------------
    # Funcionalidad extra 1: simulador "¿qué pasa si cotizo más semanas?"
    #
    # Esto NO se vio en clase: usa un Slider de Kivy con un evento
    # 'on_value' que recalcula la pensión en vivo, sin tocar el modelo,
    # reutilizando el mismo controlador con una copia de los datos
    # (dataclasses.replace) que solo cambia las semanas cotizadas.
    # ------------------------------------------------------------------
    def _habilitar_simulador(self) -> None:
        self.slider_semanas_extra.disabled = False
        self.slider_semanas_extra.value = 0
        self.boton_guardar.disabled = False
        self._actualizar_texto_simulador(semanas_extra=0)

    def _deshabilitar_simulador(self) -> None:
        self.slider_semanas_extra.disabled = True
        self.slider_semanas_extra.value = 0
        self.etiqueta_simulador.text = (
            "Simulador: calcule una pensión primero para habilitarlo."
        )

    def _simular_semanas_adicionales(self, _slider: Slider, valor: float) -> None:
        if self._ultimos_datos is None:
            return
        self._actualizar_texto_simulador(semanas_extra=int(valor))

    def _actualizar_texto_simulador(self, semanas_extra: int) -> None:
        datos_simulados = replace(
            self._ultimos_datos,
            semanas_cotizadas=self._ultimos_datos.semanas_cotizadas + semanas_extra,
        )
        try:
            resultado_simulado = self.controlador.calcular(datos=datos_simulados)
        except ErrorCalculoPension:
            self.etiqueta_simulador.text = (
                "No fue posible simular ese escenario con los datos actuales."
            )
            return

        pension_simulada = formatear_miles(valor=resultado_simulado.pension)
        self.etiqueta_simulador.text = (
            f"Si cotiza {semanas_extra} semanas más: pensión estimada = "
            f"${pension_simulada}"
        )

    # ------------------------------------------------------------------
    # Funcionalidad extra 2: exportar el resultado a un archivo de texto.
    #
    # Usa App.user_data_dir (carpeta de datos de la app que Kivy resuelve
    # automáticamente según el sistema operativo) para que el botón
    # funcione igual en Windows, en otro computador o en el APK de
    # Android, sin rutas fijas -> requisito de resiliencia de la entrega.
    # ------------------------------------------------------------------
    def guardar_resultado(self) -> None:
        if self._ultimo_resultado is None:
            self._mostrar_error(mensaje="Primero debe calcular una pensión.")
            return

        ruta_archivo = os.path.join(self.user_data_dir, NOMBRE_ARCHIVO_EXPORTADO)
        lineas = self.controlador.formatear_resultado(resultado=self._ultimo_resultado)
        marca_de_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open(ruta_archivo, "a", encoding="utf-8") as archivo:
                archivo.write(f"\n--- Cálculo del {marca_de_tiempo} ---\n")
                archivo.write("\n".join(lineas) + "\n")
        except OSError as error:
            self._mostrar_error(
                mensaje=(
                    "No fue posible guardar el archivo.\n"
                    f"Por qué: {error}.\n"
                    "Solución: verifique permisos de escritura en el "
                    "computador o dispositivo."
                )
            )
            return

        self._mostrar_confirmacion(
            titulo="Resultado guardado",
            mensaje=f"Se guardó en:\n{ruta_archivo}",
        )

    # ------------------------------------------------------------------
    # Presentación de resultados y errores.
    #
    # Los popups de error responden las 3 preguntas del cheat-sheet de
    # GUI: qué pasó / por qué pasó / cómo se soluciona (ya incluidas en
    # el propio mensaje de la excepción de negocio).
    # ------------------------------------------------------------------
    def _mostrar_resultados(self, resultado: ResultadoPension) -> None:
        lineas = self.controlador.formatear_resultado(resultado=resultado)
        lineas = [
            linea.replace(
                f"${resultado.ibl:,.2f}", f"${formatear_miles(valor=resultado.ibl)}"
            ).replace(
                f"${resultado.pension:,.2f}",
                f"${formatear_miles(valor=resultado.pension)}",
            )
            for linea in lineas
        ]

        self.panel_resultados.text = "\n".join(lineas)
        self.panel_resultados.color = COLOR_RESULTADO
        self.panel_resultados.bold = True

    def _mostrar_error(self, mensaje: str) -> None:
        """Muestra un popup con el error, cómo se soluciona y dónde ayudarse."""
        contenido = BoxLayout(orientation="vertical", padding=10, spacing=10)
        contenido.add_widget(
            Label(
                text=mensaje + "\n\n¿Sigue con problemas? Revise el README del "
                "proyecto o contacte al equipo.",
                color=COLOR_TEXTO,
                text_size=(320, None),
            )
        )
        boton_cerrar = Button(text="Entendido", size_hint_y=None, height=44)
        contenido.add_widget(boton_cerrar)

        popup = Popup(
            title="No fue posible calcular la pensión",
            content=contenido,
            size_hint=(None, None),
            size=(380, 260),
            auto_dismiss=True,
        )
        boton_cerrar.bind(on_release=popup.dismiss)
        popup.open()

    def _mostrar_confirmacion(self, titulo: str, mensaje: str) -> None:
        contenido = BoxLayout(orientation="vertical", padding=10, spacing=10)
        contenido.add_widget(
            Label(text=mensaje, color=COLOR_TEXTO, text_size=(320, None))
        )
        boton_cerrar = Button(text="Cerrar", size_hint_y=None, height=44)
        contenido.add_widget(boton_cerrar)

        popup = Popup(
            title=titulo,
            content=contenido,
            size_hint=(None, None),
            size=(380, 200),
        )
        boton_cerrar.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    CalculadoraPensionApp().run()
