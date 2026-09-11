# Calculadora Pensional - Régimen de Prima Media (Colombia)

Calculadora de pensión de vejez para el Régimen de Prima Media en Colombia,
desarrollada en Python con **dos interfaces de usuario (consola y GUI con Kivy)**
que comparten la misma lógica de negocio.

## Creadores del proyecto

- **Samuel Alejandro Marroquin Garces**
- (Integrante 2 - agregar nombre y código)

Repositorio (fork): https://github.com/SamuelMarroquin2009-12/Proyecto_calculadora_pensional

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
datos no son válidos y muestra mensajes de error amigables al usuario.

## Arquitectura

El proyecto usa una arquitectura **Modelo - Controlador - Vista**:

| Capa | Ubicación | Responsabilidad |
|------|-----------|-----------------|
| Modelo | `src/model/logica_pension.py` | Cálculo de la pensión, IBL, tasa de reemplazo, validaciones y excepciones |
| Controlador | `src/controller/pension_controller.py` | Coordina vistas y modelo; traduce excepciones a mensajes amigables; formatea resultados |
| Vista (consola) | `src/view/console/main.py` | Interfaz de línea de comandos |
| Vista (GUI) | `src/view/gui/main.py` | Interfaz gráfica con Kivy |

La **lógica de negocio vive únicamente en el modelo**; la consola y la GUI
la comparten a través del controlador. Ninguna vista realiza cálculos.

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
│   ├── test_pension.py      -> Pruebas del modelo (casos de Excel)
│   └── test_controller.py   -> Pruebas del controlador
│
└── README.md
```

## Entradas

- **IBC últimos 10 años** y **IBC toda la vida laboral** (pesos): el sistema
  usa el valor más favorable como IBL.
- **Salario mínimo legal vigente**: debe ser mayor que cero.
- **Semanas cotizadas**: mínimo 1300 para tener derecho a pensión.
- **Edad**: mínimo 57 años (mujeres) o 62 años (hombres).
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
inválidos se muestra un mensaje de error amigable (popup en GUI / texto en consola).

## Ejecución

Requisito: **Python 3.10+**. Para la GUI instalar dependencias:

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

Se espera: `Ran 25 tests ... OK`

## Ejecutable para Windows (PyInstaller)

```
pip install pyinstaller
pyinstaller --onefile --windowed --name CalculadoraPensional main.py
```

El ejecutable queda en `dist/CalculadoraPensional.exe`.

## App para Android (Buildozer)

```
pip install buildozer
buildozer -v android debug
```

El APK queda en la carpeta `bin/`. Requiere entorno Linux o WSL.

## Libro de casos de prueba

El archivo `doc/trabajofinalcasosdeprueba.xlsx` (mínimo 10 casos: normales,
extraordinarios y de error) se corresponde con las pruebas de
`tests/test_pension.py`.

## Control de versiones

Proyecto versionado con Git y alojado en GitHub (fork del proyecto recibido).
