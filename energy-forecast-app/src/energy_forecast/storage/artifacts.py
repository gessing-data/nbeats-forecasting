"""Filesystem conventions for generated model and forecast artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ArtifactPaths:
    """Resolved filesystem paths for one model training run."""

    root: Path
    model_dir: Path
    training_input_path: Path
    forecasts_dir: Path
    forecast_inputs_dir: Path
    forecast_runs_dir: Path


def build_run_id(now: datetime | None = None) -> str:
    current = now or datetime.now(UTC)
    return current.strftime("%Y-%m-%d_%H%M%S")


def build_artifact_paths(
    app_root: str | Path,
    *,
    dataset_name: str,
    model_name: str,
    horizon: int,
    run_id: str,
) -> ArtifactPaths:
    root = Path(app_root)
    dataset = _safe_name(dataset_name)
    model = _safe_name(model_name)
    h_segment = f"h{horizon}"
    basename = f"{dataset}_{model}_{h_segment}_{run_id}"

    return ArtifactPaths(
        root=root,
        model_dir=root / "models" / "trained" / dataset / model / h_segment / run_id,
        training_input_path=root / "data" / "training_inputs" / f"{basename}_train.csv",
        forecasts_dir=root / "data" / "forecasts",
        forecast_inputs_dir=root / "data" / "forecast_inputs",
        forecast_runs_dir=root / "data" / "forecast_runs",
    )


def save_dataframe(dataframe: pd.DataFrame, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False)
    return output_path


def save_json(payload: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return output_path


def _safe_name(value: str) -> str:
    safe = "".join(character if character.isalnum() or character in {"-", "_"} else "_" for character in value.strip())
    if not safe:
        raise ValueError("artifact name cannot be empty")
    return safe
