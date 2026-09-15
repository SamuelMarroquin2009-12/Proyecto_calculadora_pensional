"""Punto de entrada de la aplicación gráfica (GUI).

Este archivo debe vivir en la carpeta raíz del repositorio (junto al
README) para poder:

- Generar el ejecutable de Windows con PyInstaller.
- Generar el APK de Android con Buildozer (Buildozer exige que el
  archivo principal se llame exactamente ``main.py`` y esté en la raíz).

Toda la interfaz gráfica real vive en ``src/view/gui/main.py``; este
archivo solo agrega ``src`` al path de módulos e importa/ejecuta esa
aplicación, tal como lo indica el cheat-sheet de Kivy del curso.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from view.gui.main import CalculadoraPensionApp

if __name__ == "__main__":
    CalculadoraPensionApp().run()
