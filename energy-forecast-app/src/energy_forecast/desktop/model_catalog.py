import json
from pathlib import Path

from energy_forecast.app_paths import AppPaths, resolve_app_paths
from energy_forecast.data.opsd_zones import load_opsd_zone_names


ModelRecord = dict[str, object]


def list_pretrained_models(paths: AppPaths | None = None) -> list[ModelRecord]:
    app_paths = paths or resolve_app_paths()
    models_root = app_paths.models_dir
    if not models_root.exists():
        return []

    zone_names = load_opsd_zone_names(app_paths)
    models = [
        model
        for model_dir in sorted(models_root.glob("*"))
        if model_dir.is_dir()
        if (model := _load_model_record(model_dir, zone_names, models_root)) is not None
    ]
    return models


def find_pretrained_model(
    model_id: str, paths: AppPaths | None = None
) -> ModelRecord | None:
    return next(
        (model for model in list_pretrained_models(paths) if model["id"] == model_id),
        None,
    )


def _load_model_record(
    model_dir: Path, zone_names: dict[str, str], models_root: Path
) -> ModelRecord | None:
    relative_model_dir = model_dir.relative_to(models_root)
    config = _read_json(model_dir / "config.json")
    metadata = _read_json(model_dir / "metadata.json")
    if config is None or metadata is None:
        return None

    model_id = str(metadata.get("model_id") or model_dir.name)
    dataset = str(metadata.get("dataset") or model_id)
    model_type = str(metadata.get("model") or "model")
    input_size = int(config.get("input_size", 0))
    horizon = int(config.get("horizon", 0))
    max_steps = int(config.get("max_steps", 0))
    frequency = str(config.get("freq", ""))
    zone = zone_names.get(dataset, dataset)

    return {
        "id": model_id,
        "model_relative_dir": relative_model_dir.as_posix(),
        "name": f"{model_type.upper()} {zone}",
        "zone": zone,
        "zone_code": dataset,
        "dataset": dataset,
        "description": str(
            metadata.get("description") or "Modelo preentrenado disponible."
        ),
        "history_window": input_size,
        "forecast_horizon": horizon,
        "input_size": input_size,
        "horizon": horizon,
        "frequency": frequency,
        "max_steps": max_steps,
        "model_type": model_type,
        "model_dir": str(model_dir),
        "model_config": config,
        "model_metadata": metadata,
    }


def _read_json(path: Path) -> dict[str, object] | None:
    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return None

    return data if isinstance(data, dict) else None
