from __future__ import annotations

from typing import Any

import flet as ft
import flet_charts as fc
import pandas as pd

from energy_forecast.desktop.features.forecast_workspace.components.common import (
    _section_card,
)
from energy_forecast.desktop.features.forecast_workspace.constants import (
    PRIMARY_TEXT,
    SECONDARY_TEXT,
)
from energy_forecast.desktop.features.forecast_workspace.utils import (
    MAX_CHART_POINTS,
    _border,
    _downsample,
    _format_timestamp,
)


def _context_section(
    model: dict[str, object],
    context_mode: ft.Dropdown,
    datetime_controls: ft.Row,
    date_summary: ft.Text,
    summary: ft.Container,
) -> ft.Container:
    return _section_card(
        icon=ft.Icons.DATE_RANGE,
        title="Seleccion temporal",
        body="El contexto enviado al modelo tendra exactamente el input_size requerido.",
        footer=f"Contexto requerido: {model['input_size']} filas",
        extra=[context_mode, datetime_controls, date_summary, summary],
    )


def _context_summary_content(summary: dict[str, Any] | None) -> ft.Control:
    if summary is None:
        return ft.Text(
            "Selecciona una fuente para preparar el contexto.",
            size=13,
            color=SECONDARY_TEXT,
        )
    if "error" in summary:
        return ft.Text(str(summary["error"]), size=13, color="#DC2626")
    start = pd.Timestamp(summary["start"])
    end = pd.Timestamp(summary["end"])
    duration = end - start
    return ft.Container(
        width=float("inf"),
        padding=12,
        border=_border("#CBD5E1"),
        border_radius=12,
        bgcolor="#F8FAFC",
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text(
                    "Input que recibira el modelo",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=PRIMARY_TEXT,
                ),
                _context_range_row(start, end, int(summary["input_size"]), duration),
                _context_preview_chart(summary["context"]),
            ],
        ),
    )


def _context_range_row(
    start: pd.Timestamp, end: pd.Timestamp, rows: int, duration: pd.Timedelta
) -> ft.ResponsiveRow:
    return ft.ResponsiveRow(
        spacing=12,
        run_spacing=12,
        controls=[
            _context_range_item("Desde", _format_timestamp(start)),
            _context_range_item("Hasta", _format_timestamp(end)),
            _context_range_item("Cobertura", _duration_label(duration)),
            _context_range_item("Puntos", str(rows)),
        ],
    )


def _context_range_item(label: str, value: str) -> ft.Container:
    return ft.Container(
        col={"xs": 12, "sm": 6, "md": 3},
        padding=12,
        border=_border("#CBD5E1"),
        border_radius=10,
        bgcolor=ft.Colors.WHITE,
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Text(label, size=12, color=SECONDARY_TEXT),
                ft.Text(value, size=13, color=PRIMARY_TEXT, weight=ft.FontWeight.W_600),
            ],
        ),
    )


def _context_preview_chart(context: pd.DataFrame) -> ft.Control:
    if context.empty:
        return ft.Container(
            height=220,
            alignment=ft.Alignment(0, 0),
            border=_border("#CBD5E1"),
            border_radius=12,
            content=ft.Text("Sin datos para graficar.", color=SECONDARY_TEXT),
        )
    chart_df = _downsample(context, MAX_CHART_POINTS)
    min_y = float(chart_df["y"].min())
    max_y = float(chart_df["y"].max())
    y_padding = max((max_y - min_y) * 0.1, 1)
    points = [
        fc.LineChartDataPoint(
            x=index,
            y=float(row.y),
            tooltip=f"{_format_timestamp(row.timestamp)}\n{row.y}",
        )
        for index, row in enumerate(chart_df.itertuples())
    ]
    chart = fc.LineChart(
        data_series=[
            fc.LineChartData(
                points=points,
                color="#2563EB",
                stroke_width=3,
                curved=True,
                point=False,
                below_line_bgcolor="#DBEAFE",
            )
        ],
        min_x=0,
        max_x=max(len(points) - 1, 1),
        min_y=min_y - y_padding,
        max_y=max_y + y_padding,
        left_axis=fc.ChartAxis(show_labels=False),
        bottom_axis=fc.ChartAxis(show_labels=False),
        horizontal_grid_lines=fc.ChartGridLines(color="#E2E8F0", interval=y_padding),
        vertical_grid_lines=fc.ChartGridLines(
            color="#F1F5F9", interval=max(len(points) // 6, 1)
        ),
        height=240,
        expand=True,
    )
    return ft.Column(
        spacing=6,
        controls=[
            ft.Text("Valores seleccionados para el input", size=12, color=SECONDARY_TEXT),
            chart,
        ],
    )


def _duration_label(duration: pd.Timedelta) -> str:
    total_hours = int(duration.total_seconds() // 3600)
    if total_hours >= 24:
        days = total_hours // 24
        hours = total_hours % 24
        return f"{days} dias {hours} horas" if hours else f"{days} dias"
    return f"{total_hours} horas"
