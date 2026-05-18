"""N-BEATS model adapter backed by neuralforecast."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd
from neuralforecast import NeuralForecast
from neuralforecast.models import NBEATS
from pandas.tseries.frequencies import to_offset

from .base import ForecastModel


class NBeatsModel(ForecastModel):
    """Forecast model adapter that hides neuralforecast details."""

    _RESERVED_COLUMNS = {"unique_id", "ds"}

    def __init__(
        self,
        horizon: int,
        *,
        freq: str = "H",
        input_size: int | None = None,
        max_steps: int = 100,
        model_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        self._validate_horizon(horizon)

        self.horizon = horizon
        self.freq = freq
        self.input_size = input_size if input_size is not None else 2 * horizon
        self.max_steps = max_steps
        self.model_kwargs = dict(model_kwargs or {})
        self._forecaster: NeuralForecast | None = None
        self._unique_id = "series_0"

    def fit(self, series: pd.DataFrame) -> None:
        prepared = self._prepare_series(series)
        inferred_offset = self._infer_offset(prepared)
        configured_offset = to_offset(self.freq)
        if inferred_offset != configured_offset:
            raise ValueError(
                "series frequency does not match configured freq for NBeatsModel"
            )

        train_df = prepared.rename(columns={"timestamp": "ds"}).copy()
        train_df["unique_id"] = self._unique_id
        train_df = train_df.loc[:, ["unique_id", "ds", "y"]]

        nbeats_kwargs: dict[str, Any] = {
            "h": self.horizon,
            "input_size": self.input_size,
            "max_steps": self.max_steps,
        }
        nbeats_kwargs.update(self.model_kwargs)

        model = NBEATS(**nbeats_kwargs)
        self._forecaster = NeuralForecast(models=[model], freq=self.freq)
        self._forecaster.fit(df=train_df)

    def predict(self, horizon: int) -> pd.DataFrame:
        self._validate_horizon(horizon)

        if self._forecaster is None:
            raise RuntimeError("NBeatsModel must be fitted before calling predict")

        if horizon != self.horizon:
            raise ValueError(
                f"NBeatsModel was configured with horizon={self.horizon}; received {horizon}"
            )

        forecast_df = self._forecaster.predict()
        prediction_column = self._get_prediction_column(forecast_df)

        return (
            forecast_df.loc[:, ["ds", prediction_column]]
            .rename(columns={"ds": "timestamp", prediction_column: "yhat"})
            .reset_index(drop=True)
        )

    def _get_prediction_column(self, forecast_df: pd.DataFrame) -> str:
        candidates = [
            column
            for column in forecast_df.columns
            if column not in self._RESERVED_COLUMNS
            and "-lo-" not in column
            and "-hi-" not in column
        ]
        if not candidates:
            raise RuntimeError("NeuralForecast returned no point forecast column")

        return candidates[0]
