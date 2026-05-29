from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from energy_forecast.app_paths import AppPaths
from energy_forecast.data.opsd_zones import load_opsd_zone_names
from energy_forecast.storage import safe_artifact_name

from .constants import SOURCE_GROUPS
from .utils import _is_under


@dataclass(frozen=True)
class SourceInfo:
    name: str
    path: Path
    group: str


def _load_sources(paths: AppPaths, model: dict[str, object]) -> list[SourceInfo]:
    sources: list[SourceInfo] = []
    zone_names = load_opsd_zone_names(paths)
    training_source = _training_source_path(paths, model)
    if training_source is not None:
        sources.append(_source_info(training_source, "Modelo", zone_names))
    sources.extend(_directory_sources(paths.imported_data_dir, "Importado", zone_names))
    sources.extend(_directory_sources(paths.processed_data_dir, "Procesado", zone_names))
    return sources


def _import_source(source: Path, paths: AppPaths) -> Path:
    if not source.exists():
        raise ValueError("El archivo seleccionado no existe.")
    paths.imported_data_dir.mkdir(parents=True, exist_ok=True)
    target = paths.imported_data_dir / f"{safe_artifact_name(source.stem)}.csv"
    counter = 2
    while target.exists():
        target = paths.imported_data_dir / f"{safe_artifact_name(source.stem)}-{counter}.csv"
        counter += 1
    shutil.copy2(source, target)
    return target


def _validated_source(path: Path, frequency: str) -> pd.DataFrame:
    prepared = _load_source_frame(path)
    _validate_continuity(prepared, frequency)
    return prepared


def _load_source_frame(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = {"timestamp", "y"}.difference(df.columns)
    if missing:
        raise ValueError("El CSV debe incluir las columnas timestamp,y.")
    prepared = df.loc[:, ["timestamp", "y"]].copy()
    prepared["timestamp"] = pd.to_datetime(prepared["timestamp"], errors="coerce", utc=True)
    prepared["y"] = pd.to_numeric(prepared["y"], errors="coerce")
    prepared = prepared.dropna(subset=["timestamp", "y"])
    if prepared.empty:
        raise ValueError("La fuente no contiene filas validas timestamp,y.")
    return prepared.sort_values("timestamp").reset_index(drop=True)


def _available_groups(state: dict[str, object]) -> list[str]:
    return [
        group for group in SOURCE_GROUPS if any(item.group == group for item in state["sources"])
    ] or ["Procesado"]


def _ensure_active_group(state: dict[str, object]) -> None:
    groups = _available_groups(state)
    if state["active_group"] not in groups:
        state["active_group"] = groups[0]


def _source_group_title(group: str) -> str:
    labels = {
        "Modelo": "Fuente del modelo",
        "Importado": "CSV importados",
        "Procesado": "Datasets procesados",
    }
    return labels.get(group, group)


def _source_count_label(visible: int, total: int) -> str:
    if total == 0:
        return "No hay fuentes disponibles."
    if visible >= total:
        return f"Mostrando {total} fuente{'s' if total != 1 else ''}."
    return f"Mostrando {visible} de {total} fuentes. Desplazate para cargar mas."


def _validate_continuity(df: pd.DataFrame, frequency: str) -> None:
    if df["timestamp"].duplicated().any():
        raise ValueError("La fuente contiene timestamps duplicados.")
    if len(df) < 2:
        return
    timestamps = df["timestamp"].reset_index(drop=True)
    deltas = timestamps.diff().dropna()
    if (deltas <= pd.Timedelta(0)).any():
        raise ValueError("La fuente debe tener timestamps crecientes.")
    expected = pd.date_range(start=timestamps.iloc[0], periods=len(timestamps), freq=frequency)
    if not timestamps.equals(pd.Series(expected)):
        raise ValueError(
            f"La fuente no es continua para la frecuencia del modelo ({frequency})."
        )


def _directory_sources(
    directory: Path, group: str, zone_names: dict[str, str]
) -> list[SourceInfo]:
    if not directory.exists():
        return []
    paths = sorted(directory.glob("*.csv"))
    if group == "Importado":
        paths = [path for path in paths if not _is_generated_artifact(path)]
    return [_source_info(path, group, zone_names) for path in paths]


def _is_generated_artifact(path: Path) -> bool:
    return path.name.endswith(("_training_input.csv", "_forecast_input.csv"))


def _training_source_path(paths: AppPaths, model: dict[str, object]) -> Path | None:
    metadata = model.get("metadata")
    if not isinstance(metadata, dict):
        return None
    source_file = metadata.get("source_file")
    if isinstance(source_file, str) and source_file:
        candidate = Path(source_file)
        if candidate.exists() and _is_under(candidate, paths.data_dir):
            return candidate
    return None


def _source_info(path: Path, group: str, zone_names: dict[str, str]) -> SourceInfo:
    return SourceInfo(zone_names.get(path.stem, path.stem), path, group)
