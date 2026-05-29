import pandas as pd

from energy_forecast.seeders import opsd_timeseries
from energy_forecast.seeders.opsd_constants import MIN_CONTINUOUS_HOURS
from energy_forecast.seeders.opsd_timeseries import (
    longest_continuous_segment,
    normalize_zone,
)
from energy_forecast.seeders.opsd_validation import opsd_load_columns


def test_detect_opsd_load_columns() -> None:
    columns = ["utc_timestamp", "AT_load_actual_entsoe_transparency", "AT_solar_generation_actual"]

    assert opsd_load_columns(columns) == ["AT_load_actual_entsoe_transparency"]


def test_longest_continuous_segment() -> None:
    timestamps = pd.to_datetime(
        ["2020-01-01 00:00", "2020-01-01 01:00", "2020-01-03 00:00", "2020-01-03 01:00", "2020-01-03 02:00"],
        utc=True,
    )
    series = pd.DataFrame({"timestamp": timestamps, "y": [1, 2, 3, 4, 5]})

    segment = longest_continuous_segment(series)

    assert segment["y"].tolist() == [3, 4, 5]


def test_normalize_zone_omits_short_segment(monkeypatch) -> None:
    monkeypatch.setattr(opsd_timeseries, "MIN_CONTINUOUS_HOURS", 3)
    raw = pd.DataFrame(
        {
            "utc_timestamp": ["2020-01-01T00:00Z", "2020-01-01T01:00Z"],
            "AT_load_actual_entsoe_transparency": [1.0, 2.0],
        }
    )

    assert normalize_zone(raw, "AT_load_actual_entsoe_transparency").empty


def test_normalize_zone_outputs_timestamp_y(monkeypatch) -> None:
    monkeypatch.setattr(opsd_timeseries, "MIN_CONTINUOUS_HOURS", 2)
    raw = pd.DataFrame(
        {
            "utc_timestamp": ["2020-01-01T00:00Z", "2020-01-01T01:00Z"],
            "AT_load_actual_entsoe_transparency": [1.0, 2.0],
        }
    )

    dataset = normalize_zone(raw, "AT_load_actual_entsoe_transparency")

    assert list(dataset.columns) == ["timestamp", "y"]
    assert len(dataset) == 2
    assert MIN_CONTINUOUS_HOURS == 8760
