from __future__ import annotations

from pathlib import Path

import pandas as pd

from energy_forecast.seeders.opsd_constants import (
    LOAD_SUFFIX,
    MIN_CONTINUOUS_HOURS,
    UTC_TIMESTAMP_COLUMN,
)


class SeederError(RuntimeError):
    """Semantic seeding failure suitable for UI display."""


def load_columns(path: Path) -> list[str]:
    try:
        return list(pd.read_csv(path, nrows=0).columns)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise SeederError(f"No se pudo leer el encabezado de {path.name}.") from exc


def opsd_load_columns(columns: list[str]) -> list[str]:
    return [column for column in columns if column.endswith(LOAD_SUFFIX)]


def validate_raw_header(path: Path) -> list[str]:
    if not path.exists():
        raise SeederError("No existe el CSV crudo de OPSD.")
    columns = load_columns(path)
    if UTC_TIMESTAMP_COLUMN not in columns:
        raise SeederError("El CSV crudo no tiene columna utc_timestamp.")
    load_columns_ = opsd_load_columns(columns)
    if not load_columns_:
        raise SeederError("El CSV crudo no tiene columnas OPSD de demanda real.")
    return load_columns_


def parse_timestamps(values: pd.Series) -> pd.Series:
    timestamps = pd.to_datetime(values, utc=True, errors="coerce")
    if timestamps.isna().any():
        raise SeederError("El CSV crudo contiene timestamps invalidos.")
    return timestamps


def validate_processed_dataset(path: Path) -> None:
    try:
        dataset = pd.read_csv(path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise SeederError(f"No se pudo leer dataset procesado {path.name}.") from exc
    if list(dataset.columns) != ["timestamp", "y"]:
        raise SeederError(f"Dataset procesado invalido: {path.name}.")
    if len(dataset) < MIN_CONTINUOUS_HOURS:
        raise SeederError(f"Dataset procesado demasiado corto: {path.name}.")
    parse_timestamps(dataset["timestamp"])


def validate_catalog(path: Path) -> None:
    try:
        catalog = pd.read_csv(path, dtype=str).fillna("")
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise SeederError("No se pudo leer el catalogo OPSD.") from exc
    required = {"code", "name", "kind", "source_variable", "source_description"}
    if not required.issubset(catalog.columns):
        raise SeederError("El catalogo OPSD no tiene las columnas requeridas.")
    if catalog.empty or catalog["code"].eq("").any() or catalog["code"].duplicated().any():
        raise SeederError("El catalogo OPSD contiene codigos vacios o duplicados.")
