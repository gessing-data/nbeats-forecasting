import json
import shutil
from pathlib import Path

from energy_forecast.data.opsd_zones import load_opsd_zone_names


ModelRecord = dict[str, object]

APP_ROOT = Path(__file__).resolve().parents[3]
MODELS_ROOT = APP_ROOT / "models"


def list_pretrained_models() -> list[ModelRecord]:
    if not MODELS_ROOT.exists():
        return []

    zone_names = load_opsd_zone_names()
    models = [
        model
        for model_dir in sorted(MODELS_ROOT.iterdir())
        if model_dir.is_dir()
        if (model := _load_model_record(model_dir, zone_names)) is not None
    ]
    return models


def find_pretrained_model(model_id: str) -> ModelRecord | None:
    return next(
        (model for model in list_pretrained_models() if model["id"] == model_id), None
    )


def delete_pretrained_model(model_id: str) -> None:
    model = find_pretrained_model(model_id)
    if model is None:
        raise FileNotFoundError(f"Modelo no encontrado: {model_id}")
    model_dir = Path(str(model["model_dir"]))
    if not model_dir.is_relative_to(MODELS_ROOT):
        raise ValueError("La ruta del modelo no pertenece al directorio de modelos.")
    shutil.rmtree(model_dir)


def _load_model_record(
    model_dir: Path, zone_names: dict[str, str]
) -> ModelRecord | None:
    config = _read_json(model_dir / "config.json")
    metadata = _read_json(model_dir / "metadata.json")
    if config is None or metadata is None:
        return None

    dataset = str(metadata.get("dataset") or model_dir.parents[1].name)
    model_type = str(metadata.get("model") or "model")
    input_size = int(config.get("input_size", 0))
    horizon = int(config.get("horizon", 0))
    max_steps = int(config.get("max_steps", 0))
    frequency = str(config.get("freq", ""))
    zone = zone_names.get(dataset, dataset)
    title = str(metadata.get("title") or f"{model_type.upper()} {zone}")

    return {
        "id": str(metadata.get("id") or model_dir.name),
        "model_relative_dir": model_dir.name,
        "name": title,
        "title": title,
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
        "config": config,
        "metadata": metadata,
    }


def _read_json(path: Path) -> dict[str, object] | None:
    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return None

    return data if isinstance(data, dict) else None
