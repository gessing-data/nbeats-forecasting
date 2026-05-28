"""Model adapters with a shared forecasting interface."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import ForecastModel
    from .nbeats_model import NBeatsModel

__all__ = ["ForecastModel", "NBeatsModel"]


def __getattr__(name: str) -> Any:
    if name == "ForecastModel":
        return import_module(".base", __name__).ForecastModel
    if name == "NBeatsModel":
        return import_module(".nbeats_model", __name__).NBeatsModel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
