from __future__ import annotations

from datetime import date, datetime
from typing import Any

import flet as ft
import pandas as pd

from .utils import _format_timestamp


def _prepare_context_date_state(state: dict[str, Any], frame: pd.DataFrame) -> None:
    hours_by_date: dict[date, list[str]] = {}
    for timestamp in frame["timestamp"]:
        hours_by_date.setdefault(timestamp.date(), []).append(timestamp.strftime("%H:%M"))
    state["context_hours_by_date"] = hours_by_date
    state["context_start_date"] = frame["timestamp"].iloc[0].date()
    state["context_start_hour"] = frame["timestamp"].iloc[0].strftime("%H:%M")


def _configure_context_date_picker(date_picker: ft.DatePicker, state: dict[str, Any]) -> None:
    frame = state.get("source_frame")
    if frame is None or frame.empty:
        return
    first_date = frame["timestamp"].iloc[0].date()
    last_date = frame["timestamp"].iloc[-1].date()
    date_picker.first_date = first_date
    date_picker.last_date = last_date
    date_picker.current_date = first_date
    date_picker.value = state.get("context_start_date") or first_date


def _build_context_summary(state: dict[str, Any], model: dict[str, object]) -> dict[str, Any] | None:
    frame = state.get("source_frame")
    source = state.get("selected")
    if frame is None or source is None:
        return None
    input_size = int(model["input_size"])
    if len(frame) < input_size:
        return {"error": f"La fuente tiene {len(frame)} filas y requiere {input_size}."}
    mode = state.get("context_mode", "last")
    if mode == "first":
        context = frame.head(input_size)
    elif mode == "from_timestamp":
        start = _selected_context_timestamp(state)
        if start is None:
            return {"error": "Selecciona fecha y hora inicial."}
        context = frame[frame["timestamp"] >= start].head(input_size)
    else:
        context = frame.tail(input_size)
    if len(context) != input_size:
        return {
            "error": f"No hay suficientes filas desde el punto seleccionado: {len(context)} de {input_size}."
        }
    return {
        "input_size": input_size,
        "start": context["timestamp"].iloc[0],
        "end": context["timestamp"].iloc[-1],
        "context": context.reset_index(drop=True),
    }


def _context_date_label(state: dict[str, Any]) -> str:
    frame = state.get("source_frame")
    if frame is None:
        return "Selecciona una fuente."
    start_date = state.get("context_start_date")
    start_hour = state.get("context_start_hour") or "--:--"
    return f"Limites: {_format_timestamp(frame['timestamp'].iloc[0])} - {_format_timestamp(frame['timestamp'].iloc[-1])}. Inicio elegido: {start_date or '-'} {start_hour}."


def _context_date_button_label(state: dict[str, Any]) -> str:
    selected_date = state.get("context_start_date")
    if selected_date is None:
        return "Elegir fecha inicial"
    return f"Fecha: {selected_date}"


def _option_list(values: list[str]) -> list[ft.dropdown.Option]:
    return [ft.dropdown.Option(value, value) for value in values]


def _as_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, pd.Timestamp):
        return value.date()
    if hasattr(value, "date") and not isinstance(value, date):
        return value.date()
    if isinstance(value, date):
        return value
    return pd.Timestamp(value).date()


def _selected_context_timestamp(state: dict[str, Any]) -> pd.Timestamp | None:
    selected_date = state.get("context_start_date")
    selected_hour = state.get("context_start_hour")
    if selected_date is None or not selected_hour:
        return None
    return pd.Timestamp(f"{selected_date} {selected_hour}", tz="UTC")
