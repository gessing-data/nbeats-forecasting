"""Shared contract and validation helpers for forecast models."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd
from pandas.tseries.frequencies import to_offset


class ForecastModel(ABC):
    """Common interface for forecast model adapters."""

    @abstractmethod
    def fit(self, series: pd.DataFrame) -> None:
        """Train the model with a time series."""

    @abstractmethod
    def predict(self, horizon: int) -> pd.DataFrame:
        """Forecast future values for the requested horizon."""

    @staticmethod
    def _prepare_series(series: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(series, pd.DataFrame):
            raise TypeError("series must be a pandas DataFrame")

        required_columns = {"timestamp", "y"}
        missing_columns = required_columns.difference(series.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"series must include columns: {missing}")

        prepared = series.loc[:, ["timestamp", "y"]].copy()
        prepared["timestamp"] = pd.to_datetime(prepared["timestamp"], utc=True, errors="coerce")
        prepared["y"] = pd.to_numeric(prepared["y"], errors="coerce")
        prepared = prepared.dropna(subset=["timestamp", "y"])
        prepared = prepared.sort_values("timestamp").reset_index(drop=True)

        if prepared.empty:
            raise ValueError("series is empty after cleaning timestamp and y columns")

        if prepared["timestamp"].duplicated().any():
            raise ValueError("series contains duplicated timestamps")

        return prepared

    @staticmethod
    def _validate_horizon(horizon: int) -> None:
        if not isinstance(horizon, int):
            raise TypeError("horizon must be an integer")

        if horizon <= 0:
            raise ValueError("horizon must be greater than zero")

    @staticmethod
    def _infer_offset(series: pd.DataFrame):
        timestamps = series["timestamp"]
        inferred_frequency = pd.infer_freq(timestamps)
        if inferred_frequency is not None:
            return to_offset(inferred_frequency)

        if len(timestamps) < 2:
            raise ValueError("series must contain at least two timestamps to infer frequency")

        deltas = timestamps.diff().dropna()
        first_delta = deltas.iloc[0]
        if not deltas.eq(first_delta).all():
            raise ValueError("series frequency could not be inferred from timestamp column")

        return to_offset(first_delta)

    @staticmethod
    def _build_forecast_timestamps(last_timestamp: pd.Timestamp, horizon: int, offset) -> pd.DatetimeIndex:
        return pd.date_range(start=last_timestamp + offset, periods=horizon, freq=offset)
