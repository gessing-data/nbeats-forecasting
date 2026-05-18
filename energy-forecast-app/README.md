# Energy Forecast App

Aplicacion de escritorio en Python para pronosticar demanda electrica univariada a partir de series horarias. El objetivo del subproyecto es construir una herramienta que permita seleccionar datos ya procesados por pais, entrenar modelos de pronostico y comparar un modelo estadistico de referencia contra un modelo de deep learning.

El proyecto principal de investigacion se mantiene fuera de este directorio. Este directorio contiene la aplicacion, los notebooks de preparacion de datos y el paquete Python que encapsulara la logica de datos, modelos, servicios, evaluacion e interfaz grafica.

## Objetivo

La aplicacion trabajara con demanda electrica real, no con precios, generacion solar, generacion eolica ni pronosticos de demanda publicados por terceros.

El flujo previsto es:

1. Descargar o colocar el archivo crudo de Open Power System Data en `data/raw/`.
2. Usar notebooks para transformar el archivo crudo en archivos limpios por pais dentro de `data/processed/`.
3. Iniciar la aplicacion de escritorio.
4. Seleccionar un pais disponible o cargar un CSV externo compatible.
5. Elegir un modelo de pronostico.
6. Generar el forecast y revisar resultados, graficas y metricas.

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

Dependencias principales:

```text
numpy
pandas
matplotlib
flet
pmdarima
scikit-learn
neuralforecast
```

Responsabilidad de cada dependencia:

- `pandas`: carga, limpieza y manipulacion de series temporales.
- `numpy`: calculo numerico y soporte para metricas.
- `matplotlib`: graficas simples de series historicas y pronosticos.
- `flet`: interfaz grafica de escritorio.
- `pmdarima`: modelo ARIMA/SARIMA de referencia mediante `auto_arima`.
- `neuralforecast`: modelos neuronales de forecasting, especialmente N-BEATS.
- `torch`: backend de deep learning usado por `neuralforecast`.
- `scikit-learn`: utilidades y metricas complementarias.

Dependencias de desarrollo:

```text
ipykernel
```

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
├─ notebooks/
│  ├─ 01_exploration.ipynb
│  └─ 02_prepare_country_datasets.ipynb
├─ src/
│  └─ energy_forecast/
│     ├─ __init__.py
│     ├─ config/
│     ├─ data/
│     ├─ models/
│     ├─ services/
│     ├─ evaluation/
│     └─ desktop/
└─ tests/
```

Algunas carpetas todavia pueden no existir porque el proyecto esta en etapa inicial.

## Responsabilidades Por Carpeta

`data/raw/`

Contiene archivos originales descargados desde OPSD u otra fuente. No deben ser modificados manualmente.

`data/processed/`

Contendra series limpias por pais, listas para ser consumidas por la aplicacion. Cada archivo deberia tener columnas `timestamp` y `y`.

`data/forecasts/`

Contendra salidas generadas por la aplicacion, como pronosticos exportados o resultados de comparacion.

`notebooks/`

Contiene exploracion y preparacion de datos. Los notebooks pueden depender del archivo crudo, pero la aplicacion final debe consumir preferentemente datos procesados.

`src/energy_forecast/data/`

Funciones de carga, validacion y catalogo de datasets procesados.

`src/energy_forecast/models/`

Adaptadores propios alrededor de librerias externas. Aqui se encapsularan ARIMA y N-BEATS sin implementarlos desde cero.

`src/energy_forecast/services/`

Casos de uso de la aplicacion. La GUI debe llamar a estos servicios, no directamente a modelos ni notebooks.

`src/energy_forecast/evaluation/`

Metricas, particiones temporales y comparacion entre modelos.

`src/energy_forecast/desktop/`

Interfaz grafica con Flet. Esta capa debe encargarse de formularios, botones, tablas y graficas, no de entrenamiento ni prediccion directa.

`tests/`

Pruebas unitarias y de integracion para validacion de datos, metricas, servicios y adaptadores de modelos.

## Arquitectura Esperada

La GUI no debe contener logica de entrenamiento ni prediccion. El flujo recomendado es:

```text
Flet GUI
  -> Controller
  -> ForecastingService
  -> DatasetService / loaders / validators
  -> Model adapter: ARIMA o N-BEATS
  -> Evaluation metrics
  -> Resultado para la GUI
```

Esta separacion permite cambiar librerias internas sin reescribir la interfaz grafica.

## Modelos

Modelos previstos:

- ARIMA/SARIMA como referencia estadistica.
- N-BEATS como modelo de deep learning.

No se implementaran desde cero. Se encapsularan librerias existentes en clases propias con una interfaz comun, por ejemplo:

```python
class ForecastModel:
    def fit(self, series):
        raise NotImplementedError

    def predict(self, horizon: int):
        raise NotImplementedError
```

## Metricas

Metricas previstas para comparacion:

- MAE
- RMSE
- MAPE

La validacion inicial sera temporal, evitando particiones aleatorias que rompan el orden cronologico de la serie.

## Ejecucion Futura De La App

Cuando exista el modulo principal de escritorio, la ejecucion local podria tener una forma similar a:

```powershell
poetry run python -m energy_forecast.desktop.app
```

O mediante un script definido en `pyproject.toml`.

## Empaquetado En Windows

La aplicacion esta pensada para poder distribuirse como ejecutable de Windows. Flet permite construir aplicaciones de escritorio, pero el empaquetado debe tratarse como una etapa posterior, cuando la logica de datos, modelos y GUI minima ya este estable.

El hecho de que el proyecto sea un paquete Python bajo `src/energy_forecast` no impide generar un ejecutable. Al contrario, facilita que las importaciones internas sean consistentes durante desarrollo y empaquetado.

## Notas De Desarrollo

- Mantener la preparacion de datos en notebooks o scripts separados de la GUI.
- Mantener la GUI libre de logica de modelos.
- Usar `data/processed/` como fuente principal de la aplicacion.
- Aceptar CSV externos solo si cumplen el contrato `timestamp,y`.
- Evitar mezclar demanda real con precios, generacion renovable o demanda pronosticada.
- Preferir cambios pequenos y verificables antes de construir la interfaz completa.
