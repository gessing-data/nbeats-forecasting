# Energy Forecast App

Aplicacion de escritorio en Python para pronosticar demanda electrica univariada a partir de series horarias. El objetivo del subproyecto es construir una herramienta que permita seleccionar modelos N-BEATS preentrenados y generar pronosticos sobre demanda electrica.

El proyecto principal de investigacion se mantiene fuera de este directorio. Este directorio contiene la aplicacion y el paquete Python que encapsulara la logica de datos, modelos, servicios, evaluacion e interfaz grafica. Los notebooks de exploracion y preparacion de datos viven en `../notebooks/` y usan un entorno Poetry separado.

## Objetivo

La aplicacion trabajara con demanda electrica real, no con precios, generacion solar, generacion eolica ni pronosticos de demanda publicados por terceros.

El flujo previsto es:

1. Descargar o colocar el archivo crudo de Open Power System Data en `data/raw/`.
2. Usar los notebooks de `../notebooks/` para transformar el archivo crudo en archivos limpios por pais dentro de `data/processed/`.
3. Iniciar la aplicacion de escritorio.
4. Seleccionar un modelo N-BEATS preentrenado disponible.
5. Trabajar con el modelo seleccionado en el espacio de forecast de la aplicacion.
6. Generar el forecast y revisar los resultados visuales.

## Fuente De Datos

La fuente de datos considerada inicialmente es Open Power System Data:

```text
https://data.open-power-system-data.org/time_series/2020-10-06/
```

El archivo base esperado es:

```text
data/raw/time_series_60min_singleindex.csv
```

La columna temporal del archivo crudo es:

```text
utc_timestamp
```

Las columnas objetivo son aquellas que terminan en:

```text
_load_actual_entsoe_transparency
```

Ejemplos:

```text
DE_load_actual_entsoe_transparency
FR_load_actual_entsoe_transparency
ES_load_actual_entsoe_transparency
```

## Datos Procesados

La aplicacion no debe depender directamente del CSV crudo de OPSD. Los datos que consumira la interfaz deben estar limpios y normalizados en `data/processed/`.

Formato recomendado por archivo:

```csv
timestamp,y
2015-01-01 00:00:00+00:00,42435.0
2015-01-01 01:00:00+00:00,41420.0
```

Convencion recomendada de nombres:

```text
data/processed/DE.csv
data/processed/FR.csv
data/processed/ES.csv
```

La aplicacion podra detectar estos archivos y ofrecer al usuario los paises disponibles. Si no hay datos procesados, o si el usuario desea trabajar con otra serie, la GUI podra permitir cargar un CSV externo con el mismo contrato: columnas `timestamp` y `y`.

## Stack Tecnologico

El proyecto usa Python con Poetry.

Version de Python recomendada:

```text
Python >=3.11,<3.13
```

Se recomienda Python 3.12 para desarrollo local en Windows, porque ofrece mejor compatibilidad con el stack cientifico y de deep learning que versiones mas recientes como Python 3.14.

Dependencias principales de la aplicacion:

```text
numpy
pandas
flet
neuralforecast
torch
flet-charts
plotly
```

Responsabilidad de cada dependencia:

- `pandas`: carga, limpieza y manipulacion de series temporales.
- `numpy`: calculo numerico para el procesamiento de datos.
- `flet`: interfaz grafica de escritorio.
- `neuralforecast`: modelos neuronales de forecasting, especialmente N-BEATS.
- `torch`: backend de deep learning usado por `neuralforecast`.
- `flet-charts`: componentes de graficacion integrados con Flet.
- `plotly`: visualizaciones interactivas para la interfaz.

Dependencias de notebooks y experimentacion:

```text
matplotlib
pmdarima
ipykernel
notebook
```

Estas dependencias se administran desde `../notebooks/pyproject.toml`, no desde el entorno de la aplicacion.

## Instalacion

Desde este directorio:

```powershell
poetry install
```

Verificar el interprete activo del entorno:

```powershell
poetry run python --version
```

Si Poetry no esta usando Python 3.12, configurar el interprete explicitamente:

```powershell
poetry env use "C:\Python312\python.exe"
poetry install
```

## Ejecucion En Desarrollo

Ejecutar la aplicacion instalada como paquete, desde este directorio:

```powershell
poetry run app
```

Ejecutar la aplicacion con hot-reload usando Poetry:

```powershell
poetry run flet run -r
```

Ejecutar la aplicacion con hot-reload desde un entorno Python ya activado:

```powershell
flet run -r
```

El comando de hot-reload usa la configuracion de Flet:

```toml
[tool.flet.app]
path = "src"
```

Por esa razon existe `src/main.py`: es una entrada tecnica para Flet CLI, hot-reload y build. La aplicacion real vive en `src/energy_forecast/desktop/app.py`, y Poetry ejecuta directamente `energy_forecast.desktop.app:run_app` mediante el script `app`.

## Estructura Del Proyecto

Estructura actual y prevista:

```text
energy-forecast-app/
├─ README.md
├─ pyproject.toml
├─ poetry.lock
├─ data/
│  ├─ raw/
│  │  └─ time_series_60min_singleindex.csv
│  ├─ processed/
│  │  ├─ DE.csv
│  │  └─ FR.csv
│  └─ forecasts/
├─ src/
│  ├─ main.py
│  └─ energy_forecast/
│     ├─ __init__.py
│     ├─ config/
│     ├─ data/
│     ├─ models/
│     ├─ services/
│     ├─ evaluation/
│     └─ desktop/
│        ├─ app.py
│        ├─ components/
│        │  ├─ app_navigation.py
│        │  └─ model_card.py
│        └─ pages/
│           ├─ model_selection_page.py
│           ├─ forecast_workspace_page.py
│           ├─ forecast_history_page.py
│           └─ settings_page.py
└─ tests/
```

Algunas carpetas todavia pueden no existir porque el proyecto esta en etapa inicial.

Los notebooks se ubican fuera de la aplicacion:

```text
nbeats-forecasting/
├─ notebooks/
│  ├─ pyproject.toml
│  ├─ 01_exploration.ipynb
│  └─ 02_prepare_country_datasets.ipynb
└─ energy-forecast-app/
```

## Responsabilidades Por Carpeta

`data/raw/`

Contiene archivos originales descargados desde OPSD u otra fuente. No deben ser modificados manualmente.

`data/processed/`

Contendra series limpias por pais, listas para ser consumidas por la aplicacion. Cada archivo deberia tener columnas `timestamp` y `y`.

`data/forecasts/`

Contendra salidas generadas por la aplicacion, como pronosticos exportados.

`../notebooks/`

Contiene exploracion y preparacion de datos. Los notebooks pueden depender del archivo crudo, pero la aplicacion final debe consumir preferentemente datos procesados.

Este directorio tiene su propio `pyproject.toml` con `package-mode = false`, porque no representa un paquete instalable. Sirve para preparar un entorno virtual separado para notebooks sin mezclar dependencias experimentales con la aplicacion.

`src/main.py`

Entrada minima esperada por Flet cuando se usa `[tool.flet.app] path = "src"`. No debe contener logica de negocio ni componentes grandes; solo debe delegar en la aplicacion real.

`src/energy_forecast/`

Paquete Python real de la aplicacion. Esta estructura permite importaciones internas consistentes, instalacion con Poetry, pruebas y empaquetado posterior como ejecutable.

`src/energy_forecast/data/`

Funciones de carga, validacion y catalogo de datasets procesados.

`src/energy_forecast/models/`

Adaptadores propios alrededor de librerias externas. Aqui se encapsulara N-BEATS sin implementarlo desde cero.

`src/energy_forecast/services/`

Casos de uso de la aplicacion. La GUI debe llamar a estos servicios, no directamente a modelos ni notebooks.

`src/energy_forecast/evaluation/`

Directorio previsto para validaciones experimentales fuera del flujo principal inicial de la interfaz.

`src/energy_forecast/desktop/`

Interfaz grafica con Flet. Esta capa debe encargarse de formularios, botones, tablas, graficas y navegacion, no de entrenamiento ni prediccion directa.

`src/energy_forecast/desktop/app.py`

Aplicacion Flet real. Debe configurar la ventana principal y montar la primera pagina, evitando acumular componentes grandes o logica de negocio.

`src/energy_forecast/desktop/pages/`

Pantallas completas de la aplicacion. Una pagina representa una vista principal que el usuario puede abrir, por ejemplo inicio, configuracion de pronostico o resultados.

`src/energy_forecast/desktop/components/`

Piezas visuales reutilizables dentro de una o varias paginas, como tarjetas, selectores, tablas o contenedores de graficas.

`src/energy_forecast/desktop/controllers/`

Directorio previsto para controladores de eventos cuando la interfaz crezca. Estos controladores conectaran acciones de Flet con servicios de aplicacion, por ejemplo ejecutar un pronostico al presionar un boton.

`tests/`

Pruebas unitarias y de integracion para validacion de datos, servicios y adaptadores de modelos.

## Arquitectura Esperada

La GUI no debe contener logica de entrenamiento ni prediccion. El flujo recomendado es:

```text
Flet GUI
  -> Controller
  -> ForecastingService
  -> DatasetService / loaders / validators
  -> Model adapter: N-BEATS
  -> Resultado para la GUI
```

Esta separacion permite cambiar librerias internas sin reescribir la interfaz grafica.

Dentro de la capa `desktop/`, la separacion recomendada es:

```text
desktop/app.py
  -> pages/model_selection_page.py
  -> pages/forecast_workspace_page.py
  -> pages/forecast_history_page.py
  -> pages/settings_page.py
  -> components/app_navigation.py
  -> components/model_card.py
```

Cuando existan mas pantallas, la estructura puede crecer sin mezclar toda la interfaz en un solo archivo:

```text
desktop/
  -> pages/
  -> components/
  -> controllers/
```

Las paginas deben componer controles visuales. Los componentes deben ser piezas reutilizables. Los controladores deben coordinar eventos de la GUI con servicios como `ForecastingService`.

## Modelos

Modelo previsto para la aplicacion:

- N-BEATS como modelo principal de forecasting.

La seleccion de modelos en la interfaz corresponde a modelos N-BEATS preentrenados. Cada modelo representa una configuracion entrenada para una serie especifica, por ejemplo pais, ventana historica de entrada, horizonte de pronostico y frecuencia temporal.

No se implementaran desde cero. Se encapsularan librerias existentes en clases propias con una interfaz comun, por ejemplo:

```python
class ForecastModel:
    def fit(self, series):
        raise NotImplementedError

    def predict(self, horizon: int):
        raise NotImplementedError
```

## Empaquetado En Windows

La aplicacion esta pensada para poder distribuirse como ejecutable de Windows. Flet permite construir aplicaciones de escritorio, pero el empaquetado debe tratarse como una etapa posterior, cuando la logica de datos, modelos y GUI minima ya este estable.

El hecho de que el proyecto sea un paquete Python bajo `src/energy_forecast` no impide generar un ejecutable. Al contrario, facilita que las importaciones internas sean consistentes durante desarrollo y empaquetado.

Build futuro orientativo desde este directorio:

```powershell
poetry run flet build windows
```

## Notas De Desarrollo

- Mantener la preparacion de datos en notebooks o scripts separados de la GUI.
- Mantener la GUI libre de logica de modelos.
- Usar `data/processed/` como fuente principal de la aplicacion.
- Aceptar CSV externos solo si cumplen el contrato `timestamp,y`.
- Evitar mezclar demanda real con precios, generacion renovable o demanda pronosticada.
- Preferir cambios pequenos y verificables antes de construir la interfaz completa.
