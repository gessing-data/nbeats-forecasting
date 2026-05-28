# Energy Forecast App

Aplicacion de escritorio en Python para pronosticar demanda electrica univariada a partir de series horarias. El objetivo del subproyecto es construir una herramienta que permita seleccionar modelos N-BEATS preentrenados y generar pronosticos sobre demanda electrica.

Este directorio contiene la aplicacion y el paquete Python que encapsula la logica de datos, modelos, servicios, almacenamiento e interfaz grafica.

Los datos de trabajo ya no forman parte de la estructura de archivos del subproyecto. La aplicacion crea y usa un workspace externo visible para el usuario, por defecto en `~/Energy Forecast app/`.

## Objetivo

La aplicacion trabajara con demanda electrica real, no con precios, generacion solar, generacion eolica ni pronosticos de demanda publicados por terceros.

El flujo previsto es:

1. Descargar o colocar el archivo crudo de Open Power System Data en `~/Energy Forecast app/data/raw/`.
2. Usar los seeders futuros de la app para transformar el archivo crudo en archivos limpios por pais dentro del workspace externo.
3. Iniciar la aplicacion de escritorio.
4. Seleccionar un modelo N-BEATS preentrenado disponible.
5. Trabajar con el modelo seleccionado en el espacio de forecast de la aplicacion.
6. Generar el forecast y revisar los resultados visuales.

## Fuente De Datos

La fuente de datos considerada inicialmente es Open Power System Data:

```text
https://data.open-power-system-data.org/time_series/2020-10-06/
```

El archivo base esperado, cuando se prepare desde el workspace externo de la app, es:

```text
~/Energy Forecast app/data/raw/time_series_60min_singleindex.csv
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

La aplicacion no debe depender directamente del CSV crudo de OPSD. Los datos que consumira la interfaz deben estar limpios y normalizados en el workspace externo, no dentro del repositorio.

Formato recomendado por archivo:

```csv
timestamp,y
2015-01-01 00:00:00+00:00,42435.0
2015-01-01 01:00:00+00:00,41420.0
```

Convencion recomendada de nombres:

```text
~/Energy Forecast app/data/processed/DE.csv
~/Energy Forecast app/data/processed/FR.csv
~/Energy Forecast app/data/processed/ES.csv
```

La aplicacion podra detectar estos archivos y ofrecer al usuario los paises disponibles. Si no hay datos procesados, o si el usuario desea trabajar con otra serie, la GUI permite importar un CSV externo con el mismo contrato: columnas `timestamp` y `y`. Los CSV importados se copian al workspace externo.

## Workspace Externo

La aplicacion separa codigo fuente y datos de trabajo. El repositorio no debe contener un directorio `energy-forecast-app/data/` como parte de su estructura.

Workspace por defecto:

```text
~/Energy Forecast app/
```

Estructura administrada por la aplicacion:

```text
Energy Forecast app/
├─ settings.json
├─ data/
│  ├─ raw/
│  ├─ processed/
│  ├─ imported/
│  └─ reference/
└─ models/
```

Responsabilidades del workspace:

- `data/raw/`: archivos originales descargados desde OPSD u otra fuente.
- `data/processed/`: series limpias generadas para uso normal de la app.
- `data/imported/`: CSV externos importados desde la GUI.
- `data/reference/`: datasets de referencia o seeds preparados por la aplicacion.
- `models/`: artefactos de modelos entrenados, catalogos y runs asociados.
- `settings.json`: estado del workspace y banderas de inicializacion.

El codigo que resuelve estas rutas vive en `src/energy_forecast/app_paths.py`. La interfaz de configuracion muestra la ruta activa y permite abrir la carpeta del workspace.

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

Estructura actual y prevista. La interfaz Flet esta organizada por features: cada pantalla principal vive en `desktop/features/<feature>/` y puede tener sus propios componentes internos.

```text
energy-forecast-app/
├─ README.md
├─ pyproject.toml
├─ poetry.lock
├─ src/
│  ├─ main.py
│  └─ energy_forecast/
│     ├─ __init__.py
│     ├─ app_paths.py
│     ├─ config/
│     ├─ data/
│     │  └─ opsd_zones.py
│     ├─ models/
│     │  ├─ base.py
│     │  └─ nbeats_model.py
│     ├─ services/
│     │  ├─ forecasting.py
│     │  └─ training.py
│     ├─ storage/
│     │  ├─ artifacts.py
│     │  └─ model_catalog.py
│     └─ desktop/
│        ├─ app.py
│        ├─ layout.py
│        ├─ navigation.py
│        ├─ router.py
│        ├─ training_controller.py
│        ├─ components/
│        │  └─ app_navigation.py
│        └─ features/
│           ├─ model_selection/
│           │  ├─ page.py
│           │  └─ components/
│           │     ├─ model_card.py
│           │     ├─ model_filters.py
│           │     └─ model_list.py
│           ├─ model_creation/
│           │  └─ page.py
│           ├─ forecast_workspace/
│           │  └─ page.py
│           ├─ forecast_history/
│           │  └─ page.py
│           └─ settings/
│              └─ page.py
└─ tests/
```

Algunas carpetas todavia pueden no existir porque el proyecto esta en etapa inicial.

## Responsabilidades Por Carpeta

`src/main.py`

Entrada minima esperada por Flet cuando se usa `[tool.flet.app] path = "src"`. No debe contener logica de negocio ni componentes grandes; solo debe delegar en la aplicacion real.

`src/energy_forecast/`

Paquete Python real de la aplicacion. Esta estructura permite importaciones internas consistentes, instalacion con Poetry, pruebas y empaquetado posterior como ejecutable.

`src/energy_forecast/app_paths.py`

Resolucion y preparacion del workspace externo de usuario. Centraliza rutas como `data/raw/`, `data/processed/`, `data/imported/`, `data/reference/`, `models/` y `settings.json` fuera del directorio del repositorio.

`src/energy_forecast/data/`

Funciones de carga, validacion y catalogo de datasets procesados.

`src/energy_forecast/models/`

Adaptadores propios alrededor de librerias externas. Aqui se encapsulara N-BEATS sin implementarlo desde cero.

`src/energy_forecast/services/`

Casos de uso de la aplicacion. La GUI debe llamar a estos servicios, no directamente a modelos ni librerias externas.

`src/energy_forecast/storage/`

Persistencia y catalogos propios de la aplicacion, por ejemplo artefactos de modelos entrenados, nombres seguros de artefactos y metadatos disponibles para la interfaz.

`src/energy_forecast/desktop/`

Interfaz grafica con Flet. Esta capa debe encargarse de formularios, botones, tablas, graficas y navegacion, no de entrenamiento ni prediccion directa.

`src/energy_forecast/desktop/app.py`

Aplicacion Flet real. Debe configurar la ventana principal y montar la primera pagina, evitando acumular componentes grandes o logica de negocio.

`src/energy_forecast/desktop/layout.py`

Estructura visual compartida de la aplicacion. Debe contener composicion de layout comun, no reglas de negocio ni codigo especifico de un modelo.

`src/energy_forecast/desktop/router.py`

Enrutamiento entre vistas Flet. Debe decidir que pagina montar segun la ruta o accion de navegacion, manteniendo las paginas desacopladas entre si.

`src/energy_forecast/desktop/navigation.py`

Definicion de destinos de navegacion y utilidades relacionadas. Los controles visuales reutilizables de navegacion pertenecen a `desktop/components/`.

`src/energy_forecast/desktop/features/`

Modulos funcionales de la interfaz. Cada feature agrupa una pantalla principal y, si hace falta, sus componentes privados.

`src/energy_forecast/desktop/features/<feature>/page.py`

Pantalla principal de una feature. Debe componer controles visuales y delegar acciones relevantes a controladores o servicios.

`src/energy_forecast/desktop/features/<feature>/components/`

Piezas visuales usadas solo por esa feature, como tarjetas, filtros, listas o formularios internos. Si un componente empieza a usarse en varias features, puede moverse a `desktop/components/`.

`src/energy_forecast/desktop/components/`

Componentes visuales realmente compartidos por varias features, como la navegacion principal. No debe convertirse en un basurero de componentes especificos de una sola pantalla.

`src/energy_forecast/desktop/training_controller.py`

Controlador de eventos de entrenamiento usado por la interfaz. Debe conectar acciones de Flet con servicios de aplicacion sin implementar logica de entrenamiento dentro de la GUI.

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
  -> layout.py
  -> router.py
  -> navigation.py
  -> components/app_navigation.py
  -> features/model_selection/page.py
  -> features/model_selection/components/model_card.py
  -> features/model_selection/components/model_filters.py
  -> features/model_selection/components/model_list.py
  -> features/model_creation/page.py
  -> features/forecast_workspace/page.py
  -> features/forecast_history/page.py
  -> features/settings/page.py
```

Cuando existan mas pantallas, la estructura debe crecer agregando nuevas features o componentes locales, no mezclando toda la interfaz en un solo archivo:

```text
desktop/
  -> features/
     -> nueva_feature/
        -> page.py
        -> components/
  -> components/
  -> router.py
  -> layout.py
```

Las paginas deben componer controles visuales. Los componentes dentro de una feature deben permanecer cerca de la pantalla que los usa. Los componentes compartidos solo deben vivir en `desktop/components/` cuando tengan uso real en mas de una feature. Los controladores deben coordinar eventos de la GUI con servicios como `ForecastingService` o servicios de entrenamiento.

Indicaciones de organizacion para nuevas vistas y componentes:

- Crear una carpeta nueva en `desktop/features/<nombre_feature>/` para cada pantalla o flujo principal.
- Usar siempre `page.py` como entrada visual de la feature.
- Colocar en `desktop/features/<nombre_feature>/components/` los componentes que solo usa esa feature.
- Mantener `desktop/components/` para componentes compartidos entre varias features.
- Mantener `router.py` como punto de decision de rutas y no importar paginas directamente desde componentes compartidos.
- Mantener `layout.py` para composicion visual comun, no para estado de negocio.
- Evitar que las paginas llamen directamente a modelos externos o librerias de entrenamiento; deben delegar en `services/` o controladores del paquete.

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

- Mantener la preparacion de datos separada de la GUI.
- Mantener la GUI libre de logica de modelos.
- No agregar `energy-forecast-app/data/` como parte de la estructura del repositorio.
- Usar el workspace externo de la app como fuente principal de datasets y artefactos.
- Aceptar CSV externos solo si cumplen el contrato `timestamp,y`.
- Evitar mezclar demanda real con precios, generacion renovable o demanda pronosticada.
- Preferir cambios pequenos y verificables antes de construir la interfaz completa.
