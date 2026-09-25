# Calculadora Pensional - Régimen de Prima Media (Colombia)

Calculadora de pensión de vejez para el Régimen de Prima Media en Colombia,
desarrollada en Python con **dos interfaces de usuario (consola y GUI con
Kivy)** que comparten la misma lógica de negocio.

## Creadores del proyecto

- **Samuel Alejandro Marroquín Garcés**
- **Juan Pablo Gaviria Franco**
- **Repositorio (fork):** https://github.com/SamuelMarroquin2009-12/Proyecto_calculadora_pensional

## Descripción del proyecto

La aplicación permite ingresar los datos de una persona y calcular el valor
estimado de su pensión de vejez, teniendo en cuenta:

- IBC de los últimos 10 años.
- IBC de toda la vida laboral.
- Salario mínimo legal vigente (SMLMV).
- Semanas cotizadas.
- Edad.
- Sexo.

El sistema valida los datos, genera excepciones personalizadas cuando los
datos no son válidos y muestra mensajes de error amigables al usuario, tanto
en consola como en la GUI.

## Arquitectura

El proyecto usa una arquitectura **Modelo - Controlador - Vista**:

| Capa | Ubicación | Responsabilidad |
|------|-----------|-----------------|
| Modelo | `src/model/logica_pension.py` | Cálculo de la pensión, IBL, tasa de reemplazo, validaciones y excepciones |
| Controlador | `src/controller/pension_controller.py` | Coordina vistas y modelo; traduce excepciones a mensajes amigables; formatea resultados |
| Vista (consola) | `src/view/console/main.py` | Interfaz de línea de comandos |
| Vista (GUI) | `src/view/gui/main.py` | Interfaz gráfica con Kivy |

La **lógica de negocio vive únicamente en el modelo**; la consola y la GUI la
comparten a través del mismo controlador (`CalculadoraPensionController`).
Ninguna vista realiza cálculos por su cuenta.

### Estructura de carpetas

```
Proyecto_calculadora_pensional/
│
├── main.py                  -> Punto de entrada (GUI, PyInstaller, Buildozer)
├── requirements.txt         -> Dependencias (Kivy)
├── buildozer.spec           -> Configuración para app Android
│
├── src/
│   ├── model/
│   │   └── logica_pension.py
│   ├── controller/
│   │   └── pension_controller.py
│   └── view/
│       ├── console/
│       │   └── main.py
│       └── gui/
│           └── main.py
│
├── tests/
│   ├── test_pension.py      -> Pruebas del modelo (casos del Excel)
│   ├── test_controller.py   -> Pruebas del controlador
│   └── test_gui.py          -> Pruebas de la GUI (validación de campos,
│                                simulador de semanas y guardado en archivo)
│
└── README.md
```

## Entradas

- **IBC últimos 10 años** y **IBC toda la vida laboral** (pesos): el sistema
  usa el valor más favorable como IBL.
- **Salario mínimo legal vigente**: debe ser mayor que cero.
- **Semanas cotizadas**: mínimo 1300 para tener derecho a pensión. Debe
  ser un número entero (`1300` es válido, `1300.5` se rechaza con un
  mensaje amigable, tanto en consola como en la GUI).
- **Edad**: mínimo 57 años (mujeres) o 62 años (hombres). También debe
  ser un número entero (`62.9` se rechaza; `62.0` sí se acepta, porque
  no tiene parte decimal).
- **Sexo**: `M` (hombre) o `F` (mujer).

## Proceso

1. **Validación**: IBL no negativo ni cero, SMLMV positivo, semanas no
   negativas y >= 1300, edad mínima según sexo, sexo válido.
2. **IBL**: `max(IBC últimos 10 años, IBC toda la vida)`.
3. **Relación IBL/SMLMV**: cuántos salarios mínimos representa el IBL.
4. **Tasa base**: 65,5% menos 0,5 puntos por cada salario mínimo, con piso del 55%.
5. **Incremento**: +1,5 puntos por cada bloque completo de 50 semanas adicionales.
6. **Tasa total**: tasa base + incremento, con tope del 80%.
7. **Pensión**: `IBL × tasa total`, con garantía de un salario mínimo.

## Salidas

IBL calculado, relación con el SMLMV, porcentaje base, semanas adicionales,
incremento, porcentaje total y **pensión estimada**. En caso de datos
inválidos se muestra un mensaje de error amigable (popup en GUI / texto en
consola) que indica **qué pasó, por qué pasó y cómo se soluciona**.

---

## Cómo alineé el proyecto con el clean_code.md del profesor

Después de revisar mi código contra `clean_code.md` de
https://github.com/ProfeBill/cheat-sheets hice estos cambios concretos:

1. **Type hints en todas las funciones**, tanto en parámetros como en el
   valor de retorno (`def calcular_ibl(ibc_ultimos_10: float, ibc_toda_vida: float) -> float`),
   en el modelo, el controlador, la consola y la GUI.
2. **Parámetros nombrados al invocar funciones**, por ejemplo
   `controlador.construir_datos(ibc_ultimos_10=..., ibc_toda_vida=..., ...)`
   en lugar de pasar los valores solo por posición.
3. **Excepciones con contexto**: creé una excepción base
   `ErrorCalculoPension` de la que heredan todas las excepciones de negocio.
   Cada excepción ahora explica **qué pasó, por qué pasó, con qué valor
   ocurrió y cómo se soluciona** (antes el mensaje solo decía "qué pasó").
4. **Se dejó de usar `except Exception` como manejo principal**: la consola
   y la GUI ahora capturan primero `ValueError` (errores de formato) y
   luego `ErrorCalculoPension` (errores de negocio) de forma específica.
   Solo queda un `except Exception` como último recurso, documentado en el
   propio código como red de seguridad para cumplir el requisito de
   resiliencia de la actividad (que la app nunca se cierre sola), no como
   reemplazo del manejo específico.
5. **Funciones más cortas y con una sola responsabilidad**: por ejemplo,
   `calcular()` en la GUI ya no hace todo; ahora delega en
   `_leer_datos_formulario()`, `_ejecutar_calculo()`, `_guardar_ultimo_calculo()`
   y `_mostrar_resultados()`.
6. Las constantes de negocio (`SEMANAS_MINIMAS`, `TASA_REEMPLAZO_INICIAL`,
   etc.) ya estaban extraídas desde antes, así que ese punto del cheat-sheet
   ya se cumplía.

---

## Funcionalidad extra (en mis palabras)

Además de lo pedido en el enunciado, le agregué dos cosas a la GUI que no
vimos en clase:

**1. Simulador "¿qué pasa si cotizo más semanas?"**
Es un `Slider` de Kivy que aparece después de calcular una pensión. A
medida que uno mueve el control, la app recalcula la pensión en tiempo
real sumando esas semanas a las que ya cotizó, sin tocar el modelo ni
duplicar la fórmula: simplemente le manda al mismo controlador una copia
de los datos (`dataclasses.replace`) con las semanas modificadas. El
widget `Slider` y el patrón de "recalcular en cada evento" no los vimos en
el curso, solo `Button`, `TextInput` y `Spinner`; lo investigué porque me
pareció una forma más interesante de mostrarle al usuario el efecto de
seguir cotizando, en vez de que tenga que volver a llenar el formulario.

**2. Guardar el resultado en un archivo**
Agregué un botón "GUARDAR EN ARCHIVO" que escribe el resultado (con fecha y
hora) en un archivo de texto. Para que funcione igual en cualquier
computador o en el celular una vez compilada la APK, no usé una ruta fija:
usé `self.user_data_dir`, una carpeta que la propia librería Kivy calcula
automáticamente según el sistema operativo. Tampoco se explicó en clase;
lo busqué en la documentación de Kivy para que el botón fuera resiliente
(uno de los requisitos de la actividad) y no dependiera de en qué carpeta
se ejecute el programa.

---

## Ejecución

Requisito: **Python 3.10+**. Para la GUI, instalar dependencias:

```
pip install -r requirements.txt
```

### Interfaz gráfica (Kivy)

```
python src/view/gui/main.py
```
o desde la raíz:
```
python main.py
```

### Interfaz de consola

```
python src/view/console/main.py
```

### Pruebas unitarias

```
python -m unittest discover -s tests -v
```

Se espera: `Ran 40 tests ... OK`

`tests/test_pension.py` (18 pruebas) y `tests/test_controller.py` (7
pruebas) no dependen de Kivy. `tests/test_gui.py` (15 pruebas) construye
la app real de forma headless (sin mostrar ventana) para probar la
validación de campos enteros, el simulador de semanas adicionales y el
guardado en archivo; si Kivy no está instalado o el entorno no tiene
pantalla/GL disponible, esas 15 pruebas se omiten automáticamente
(`skipped`) en lugar de romper el resto de la suite.

---

## Cómo compilar y ejecutar el ejecutable de Windows (paso a paso)

1. Abrir una terminal (CMD o PowerShell) **en Windows**, en la carpeta raíz
   del proyecto.
2. Crear y activar un entorno virtual (recomendado, no obligatorio):

   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Instalar las dependencias, incluyendo PyInstaller:

   ```
   pip install -r requirements.txt
   pip install pyinstaller
   ```

4. Compilar el ejecutable desde la raíz del proyecto:

   ```
   pyinstaller --onefile --windowed --name CalculadoraPensional main.py
   ```

   - `--onefile` genera un único `.exe`.
   - `--windowed` evita que se abra una consola negra detrás de la GUI.
   - Este comando puede tardar uno o dos minutos la primera vez.

5. Al terminar, PyInstaller crea las carpetas `build/` y `dist/`. El
   ejecutable final queda en:

   ```
   dist\CalculadoraPensional.exe
   ```

6. **Para ejecutarlo**: entrar a la carpeta `dist` y hacer doble clic sobre
   `CalculadoraPensional.exe`, o desde la terminal:

   ```
   dist\CalculadoraPensional.exe
   ```

   Se abrirá la misma ventana de la calculadora, ya sin necesidad de tener
   Python instalado en ese computador.

7. `build/` y `dist/` ya están en `.gitignore`: **no se deben subir al
   repositorio**, solo se generan localmente (o se adjuntan aparte en la
   entrega si el profesor pide el `.exe`).

---

## Cómo compilar y ejecutar el APK de Android (paso a paso)

Buildozer solo compila en Linux. Si el equipo es Windows, el primer paso es
instalar WSL con Ubuntu.

### A. Preparar el entorno (una sola vez)

1. En Windows, abrir PowerShell **como administrador** e instalar WSL:

   ```
   wsl --install Ubuntu-22.04
   ```

   Reiniciar el computador cuando lo pida y crear el usuario de Ubuntu.

2. Abrir la terminal de Ubuntu (WSL) y actualizar el sistema:

   ```
   sudo apt update
   sudo apt -y upgrade
   sudo apt install -y python3-pip git zip unzip openjdk-17-jdk \
       autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
       libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
   ```

3. Instalar Buildozer y Cython:

   ```
   pip3 install --user --upgrade buildozer
   pip3 install --user --upgrade Cython==0.29.33 virtualenv
   export PATH=$PATH:~/.local/bin/
   ```

   Agregar esa última línea (`export PATH=...`) también al final del
   archivo `~/.bashrc` para no tener que repetirla cada vez.

### B. Clonar el proyecto dentro de WSL

**Importante:** clonar dentro de la partición de Linux (no en
`/mnt/c/...`), o la compilación falla o queda muy lenta.

```
cd ~
git clone https://github.com/SamuelMarroquin2009-12/Proyecto_calculadora_pensional.git
cd Proyecto_calculadora_pensional
```

### C. Compilar el APK

El repositorio ya incluye `buildozer.spec` configurado
(`requirements = python3,kivy`, `source.dir = .`), así que no es necesario
correr `buildozer init`.

```
buildozer -v android debug
```

- La primera compilación descarga el Android SDK/NDK y puede tardar entre
  20 y 40 minutos, dependiendo de la conexión.
- Si el proceso falla, `buildozer -v android debug` vuelve a mostrar el log
  completo del error (por eso se usa `-v`).

Al terminar, el APK queda en:

```
bin/calculadorapensional-1.0-arm64-v8a_armeabi-v7a-debug.apk
```

Verificar con:

```
ls bin
```

### D. Cómo instalar y ejecutar el APK en un celular Android

**Opción 1 - copiando el archivo al celular:**

1. Copiar el `.apk` a la partición de Windows para poder moverlo fácil:

   ```
   cp bin/*.apk /mnt/c/Users/TU_USUARIO/Desktop/
   ```

2. Pasar ese archivo al celular (por cable USB, por un enlace de Drive, por
   WhatsApp Web, etc.).
3. En el celular, abrir el archivo `.apk` desde el explorador de archivos.
4. Android pedirá permiso para "instalar aplicaciones de origen
   desconocido": debe aceptarse solo para esta instalación (es normal en
   APKs de desarrollo, que no vienen de Play Store).
5. Una vez instalada, la app aparece como **"Calculadora Pensional"** en el
   listado de aplicaciones del celular; se abre tocando su ícono, igual que
   cualquier otra app.

**Opción 2 - instalando directo con ADB (si el celular está conectado por
USB con la depuración USB activada):**

```
buildozer android deploy run
```

Este comando instala el APK y lo abre automáticamente en el celular
conectado, sin tener que copiar el archivo manualmente.

### E. Notas

- El `.gitignore` del proyecto debe incluir `.buildozer/`, `bin/`, `build/`
  y `dist/`: son carpetas generadas automáticamente y no deben subirse al
  repositorio.
- Si se necesita volver a compilar desde cero (por ejemplo, tras cambiar
  `buildozer.spec`), se puede limpiar con `buildozer android clean` antes
  de repetir el paso C.

---

## Libro de casos de prueba

El archivo `doc/trabajofinalcasosdeprueba.xlsx` (mínimo 10 casos: normales,
extraordinarios y de error) se corresponde con las pruebas de
`tests/test_pension.py`.

## Control de versiones

Proyecto versionado con Git y alojado en GitHub (fork del proyecto
recibido). La GUI se agregó en una rama de trabajo separada y luego se
integró a `main`, manteniendo la consola y las pruebas unitarias intactas
en todo momento.
