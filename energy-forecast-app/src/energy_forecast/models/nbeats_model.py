"""N-BEATS model adapter backed by neuralforecast."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

import pandas as pd
from neuralforecast import NeuralForecast
from neuralforecast.models import NBEATS
from pandas.tseries.frequencies import to_offset

from .base import ForecastModel


class NBeatsModel(ForecastModel):
    """Forecast model adapter that hides neuralforecast details."""

    _RESERVED_COLUMNS = {"unique_id", "ds"}
    _CONFIG_FILE = "config.json"
    _FORECASTER_DIR = "neuralforecast"

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
        if input_size is not None and (not isinstance(input_size, int) or input_size <= 0):
            raise ValueError("input_size must be a positive integer")
        if not isinstance(max_steps, int) or max_steps <= 0:
            raise ValueError("max_steps must be a positive integer")

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
        if not hasattr(self._forecaster, "dataset"):
            raise RuntimeError(
                "NBeatsModel was loaded without its training dataset; use predict_from_context"
            )

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

    def predict_from_context(self, context: pd.DataFrame, horizon: int) -> pd.DataFrame:
        """Forecast from a supplied historical context instead of the fitted dataset."""
        self._validate_horizon(horizon)

        if self._forecaster is None:
            raise RuntimeError("NBeatsModel must be fitted before calling predict_from_context")

        if horizon != self.horizon:
            raise ValueError(
                f"NBeatsModel was configured with horizon={self.horizon}; received {horizon}"
            )

        prepared = self._prepare_series(context)
        if len(prepared) < self.input_size:
            raise ValueError(
                f"context must include at least input_size={self.input_size} rows"
            )

        inferred_offset = self._infer_offset(prepared)
        configured_offset = to_offset(self.freq)
        if inferred_offset != configured_offset:
            raise ValueError(
                "context frequency does not match configured freq for NBeatsModel"
            )

        predict_df = prepared.rename(columns={"timestamp": "ds"}).copy()
        predict_df["unique_id"] = self._unique_id
        predict_df = predict_df.loc[:, ["unique_id", "ds", "y"]]

        forecast_df = self._forecaster.predict(df=predict_df)
        prediction_column = self._get_prediction_column(forecast_df)

        return (
            forecast_df.loc[:, ["ds", prediction_column]]
            .rename(columns={"ds": "timestamp", prediction_column: "yhat"})
            .reset_index(drop=True)
        )

    def save(self, path: str | Path, *, overwrite: bool = False) -> None:
        """Persist the fitted NeuralForecast model and wrapper configuration."""
        if self._forecaster is None:
            raise RuntimeError("NBeatsModel must be fitted before calling save")

        artifact_path = Path(path)
        artifact_path.mkdir(parents=True, exist_ok=True)

        config = {
            "horizon": self.horizon,
            "freq": self.freq,
            "input_size": self.input_size,
            "max_steps": self.max_steps,
            "model_kwargs": self.model_kwargs,
        }
        self._forecaster.save(
            path=str(artifact_path / self._FORECASTER_DIR),
            save_dataset=False,
            overwrite=overwrite,
        )
        config_path = artifact_path / self._CONFIG_FILE
        config_path.write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "NBeatsModel":
        """Load a persisted NBeatsModel artifact."""
        artifact_path = Path(path)
        config_path = artifact_path / cls._CONFIG_FILE
        if not config_path.exists():
            raise FileNotFoundError(f"NBeatsModel config not found: {config_path}")

        config = json.loads(config_path.read_text(encoding="utf-8"))
        model = cls(
            horizon=config["horizon"],
            freq=config.get("freq", "H"),
            input_size=config.get("input_size"),
            max_steps=config.get("max_steps", 100),
            model_kwargs=config.get("model_kwargs", {}),
        )
        model._forecaster = NeuralForecast.load(str(artifact_path / cls._FORECASTER_DIR))
        return model

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
