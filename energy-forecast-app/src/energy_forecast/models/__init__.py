"""Model adapters with a shared forecasting interface."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .arima_model import ArimaModel
    from .base import ForecastModel
    from .nbeats_model import NBeatsModel

__all__ = ["ForecastModel", "ArimaModel", "NBeatsModel"]


def __getattr__(name: str) -> Any:
    if name == "ForecastModel":
        return import_module(".base", __name__).ForecastModel
    if name == "ArimaModel":
        return import_module(".arima_model", __name__).ArimaModel
    if name == "NBeatsModel":
        return import_module(".nbeats_model", __name__).NBeatsModel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
