from __future__ import annotations

import flet as ft
import numpy as np
import pandas as pd


MAX_CHART_POINTS = 200


def _border(color: str) -> ft.Border:
    side = ft.BorderSide(1, color)
    return ft.Border(side, side, side, side)


def _downsample(df: pd.DataFrame, max_points: int) -> pd.DataFrame:
    if len(df) <= max_points:
        return df
    indices = np.linspace(0, len(df) - 1, max_points, dtype=int)
    return df.iloc[indices].reset_index(drop=True)


def _format_timestamp(value: pd.Timestamp) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_convert(None)
    return timestamp.strftime("%Y-%m-%d %H:%M")


def _is_under(path, root) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True
