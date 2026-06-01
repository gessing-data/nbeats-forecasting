"""Application services that orchestrate data, models, and artifacts."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .forecasting import ForecastRunResult
    from .training import TrainingResult

__all__ = [
    "ForecastRunResult",
    "TrainingResult",
    "generate_nbeats_forecast",
    "select_training_data",
    "train_nbeats_model",
]


def __getattr__(name: str) -> Any:
    if name in {"ForecastRunResult", "generate_nbeats_forecast"}:
        module = import_module(".forecasting", __name__)
        return getattr(module, name)
    if name in {"TrainingResult", "select_training_data", "train_nbeats_model"}:
        module = import_module(".training", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
