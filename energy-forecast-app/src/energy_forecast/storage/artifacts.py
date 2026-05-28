"""Filesystem conventions for generated model and forecast artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd


@dataclass(frozen=True)
class ArtifactPaths:
    """Resolved filesystem paths for one model training run."""

    root: Path
    model_id: str
    model_dir: Path
    forecasts_dir: Path
    forecast_inputs_dir: Path
    forecast_runs_dir: Path


def build_run_id(now: datetime | None = None) -> str:
    current = now or datetime.now(UTC)
    return current.strftime("%Y-%m-%d_%H%M%S_%f")


def build_model_id(models_root: str | Path, model_id: str | None = None) -> str:
    if model_id is not None:
        safe_model_id = safe_artifact_name(model_id)
        if (Path(models_root) / safe_model_id).exists():
            raise FileExistsError(f"model id already exists: {safe_model_id}")
        return safe_model_id

    root = Path(models_root)
    for _ in range(5):
        candidate = str(uuid4())
        if not (root / candidate).exists():
            return candidate
    raise FileExistsError("could not generate a unique model id")


def build_artifact_paths(
    app_root: str | Path,
    *,
    model_id: str | None = None,
) -> ArtifactPaths:
    root = Path(app_root)
    models_root = root / "models"
    resolved_model_id = build_model_id(models_root, model_id)

    return ArtifactPaths(
        root=root,
        model_id=resolved_model_id,
        model_dir=models_root / resolved_model_id,
        forecasts_dir=root / "data" / "forecasts",
        forecast_inputs_dir=root / "data" / "forecast_inputs",
        forecast_runs_dir=root / "data" / "forecast_runs",
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
