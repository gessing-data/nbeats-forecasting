"""ARIMA model adapter backed by pmdarima."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd
from pmdarima import auto_arima

from .base import ForecastModel


class ArimaModel(ForecastModel):
    """Forecast model adapter that hides pmdarima details."""

    def __init__(
        self,
        *,
        seasonal: bool = False,
        m: int = 1,
        auto_arima_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        self.seasonal = seasonal
        self.m = m
        self.auto_arima_kwargs = dict(auto_arima_kwargs or {})
        self._model = None
        self._last_timestamp: pd.Timestamp | None = None
        self._offset = None

    def fit(self, series: pd.DataFrame) -> None:
        prepared = self._prepare_series(series)

        model_kwargs: dict[str, Any] = {
            "seasonal": self.seasonal,
            "m": self.m,
            "suppress_warnings": True,
            "error_action": "raise",
            "stepwise": True,
        }
        model_kwargs.update(self.auto_arima_kwargs)

        self._model = auto_arima(prepared["y"].to_numpy(dtype=float), **model_kwargs)
        self._last_timestamp = prepared["timestamp"].iloc[-1]
        self._offset = self._infer_offset(prepared)

    def predict(self, horizon: int) -> pd.DataFrame:
        self._validate_horizon(horizon)

        if self._model is None or self._last_timestamp is None or self._offset is None:
            raise RuntimeError("ArimaModel must be fitted before calling predict")

        predictions = self._model.predict(n_periods=horizon)
        forecast_timestamps = self._build_forecast_timestamps(self._last_timestamp, horizon, self._offset)

        return pd.DataFrame(
            {
                "timestamp": forecast_timestamps,
                "yhat": pd.Series(predictions, dtype="float64"),
            }
        )
