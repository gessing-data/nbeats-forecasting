"""Filesystem conventions for generated model and forecast artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import secrets
import string
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ArtifactPaths:
    """Resolved filesystem paths for one model training run."""

    root: Path
    model_id: str
    model_dir: Path
    training_input_path: Path
    metadata_path: Path


@dataclass(frozen=True)
class ForecastArtifactPaths:
    """Resolved filesystem paths for one forecast run."""

    root: Path
    model_id: str
    run_id: str
    run_dir: Path
    forecast_input_path: Path
    forecast_path: Path
    metadata_path: Path


ID_ALPHABET = string.ascii_letters + string.digits


def build_model_id() -> str:
    return build_short_id("mdl")


def build_run_id() -> str:
    return build_short_id("run")


def build_short_id(prefix: str, size: int = 8) -> str:
    if not prefix:
        raise ValueError("id prefix cannot be empty")
    token = "".join(secrets.choice(ID_ALPHABET) for _ in range(size))
    return f"{safe_artifact_name(prefix)}_{token}"


def build_artifact_paths(
    app_root: str | Path,
    *,
    model_id: str | None = None,
) -> ArtifactPaths:
    root = Path(app_root)
    resolved_model_id = safe_artifact_name(model_id or build_model_id())
    model_dir = root / "models" / resolved_model_id

    return ArtifactPaths(
        root=root,
        model_id=resolved_model_id,
        model_dir=model_dir,
        training_input_path=root / "data" / "imported" / f"{resolved_model_id}_training_input.csv",
        metadata_path=model_dir / "metadata.json",
    )


def build_forecast_artifact_paths(
    app_root: str | Path,
    *,
    model_id: str,
    run_id: str | None = None,
) -> ForecastArtifactPaths:
    root = Path(app_root)
    resolved_model_id = safe_artifact_name(model_id)
    resolved_run_id = safe_artifact_name(run_id or build_run_id())
    run_dir = root / "models" / resolved_model_id / "runs" / resolved_run_id

    return ForecastArtifactPaths(
        root=root,
        model_id=resolved_model_id,
        run_id=resolved_run_id,
        run_dir=run_dir,
        forecast_input_path=root / "data" / "imported" / f"{resolved_run_id}_forecast_input.csv",
        forecast_path=run_dir / "forecast.csv",
        metadata_path=run_dir / "metadata.json",
    )


def save_dataframe(dataframe: pd.DataFrame, path: str | Path, *, overwrite: bool = False) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"artifact already exists: {output_path}")
    dataframe.to_csv(output_path, index=False)
    return output_path


def save_json(payload: dict[str, Any], path: str | Path, *, overwrite: bool = False) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"artifact already exists: {output_path}")
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return output_path


def safe_artifact_name(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("artifact name must be a string")

    safe = "".join(character if character.isalnum() or character in {"-", "_"} else "_" for character in value.strip())
    if not safe:
        raise ValueError("artifact name cannot be empty")
    return safe
