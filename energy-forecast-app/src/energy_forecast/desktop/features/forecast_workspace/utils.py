from __future__ import annotations

import flet as ft
import pandas as pd


def _border(color: str) -> ft.Border:
    side = ft.BorderSide(1, color)
    return ft.Border(side, side, side, side)


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
