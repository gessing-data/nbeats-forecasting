from __future__ import annotations

from pathlib import Path

import pandas as pd

from energy_forecast.seeders.opsd_constants import (
    LOAD_SUFFIX,
    MIN_CONTINUOUS_HOURS,
    UTC_TIMESTAMP_COLUMN,
)
from energy_forecast.seeders.opsd_validation import SeederError, parse_timestamps


def zone_code_from_column(column: str) -> str:
    return column.removesuffix(LOAD_SUFFIX)


def longest_continuous_segment(series: pd.DataFrame) -> pd.DataFrame:
    if series.empty:
        return series
    ordered = series.sort_values("timestamp").drop_duplicates("timestamp")
    breaks = ordered["timestamp"].diff() != pd.Timedelta(hours=1)
    groups = breaks.cumsum()
    lengths = groups.value_counts(sort=False)
    best_group = lengths.idxmax()
    return ordered.loc[groups == best_group].reset_index(drop=True)


def normalize_zone(raw: pd.DataFrame, column: str) -> pd.DataFrame:
    timestamps = parse_timestamps(raw[UTC_TIMESTAMP_COLUMN])
    values = pd.to_numeric(raw[column], errors="coerce")
    prepared = pd.DataFrame({"timestamp": timestamps, "y": values}).dropna(subset=["y"])
    segment = longest_continuous_segment(prepared)
    if len(segment) < MIN_CONTINUOUS_HOURS:
        return pd.DataFrame(columns=["timestamp", "y"])
    return segment[["timestamp", "y"]]


def process_opsd_timeseries(raw_path: Path, processed_dir: Path) -> list[str]:
    try:
        raw = pd.read_csv(raw_path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise SeederError("No se pudo leer el CSV crudo de OPSD.") from exc
    if UTC_TIMESTAMP_COLUMN not in raw.columns:
        raise SeederError("El CSV crudo no tiene columna utc_timestamp.")
    columns = [column for column in raw.columns if column.endswith(LOAD_SUFFIX)]
    if not columns:
        raise SeederError("No hay columnas OPSD de demanda real para procesar.")
    processed_dir.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []
    for column in columns:
        dataset = normalize_zone(raw, column)
        if dataset.empty:
            continue
        code = zone_code_from_column(column)
        output = dataset.copy()
        output["timestamp"] = output["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        output.to_csv(processed_dir / f"{code}.csv", index=False)
        generated.append(code)
    if not generated:
        raise SeederError("No se pudo generar ningun dataset con 8760 horas continuas.")
    return sorted(generated)
