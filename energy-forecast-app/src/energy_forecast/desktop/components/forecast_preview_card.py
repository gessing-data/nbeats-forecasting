from __future__ import annotations

from typing import Any

import flet as ft
import flet_charts as fc
import pandas as pd


PRIMARY_TEXT = "#0F172A"
SECONDARY_TEXT = "#64748B"
CONTEXT_CHART_COLOR = "#2563EB"
FORECAST_CHART_COLOR = "#F97316"


def forecast_preview_card(
    *,
    context_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    forecast_start: str,
    forecast_end: str,
    horizon: int,
    input_size: int,
) -> ft.Control:
    if forecast_df.empty:
        return ft.Text("No hay datos de preview disponibles.", size=13, color=SECONDARY_TEXT)

    return ft.Container(
        width=float("inf"),
        border=_border("#CBD5E1"),
        border_radius=12,
        padding=12,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Text(
                    "Forecast generado",
                    size=13,
                    weight=ft.FontWeight.W_600,
                    color=PRIMARY_TEXT,
                ),
                _forecast_metric_grid(
                    forecast_start=forecast_start,
                    forecast_end=forecast_end,
                    horizon=horizon,
                    input_size=input_size,
                ),
                ft.Text("Valores de contexto y pronostico", size=12, color=SECONDARY_TEXT),
                _forecast_preview_legend(show_context=not context_df.empty),
                _forecast_chart(context_df, forecast_df),
            ],
        ),
    )


def _forecast_metric_grid(
    *,
    forecast_start: str,
    forecast_end: str,
    horizon: int,
    input_size: int,
) -> ft.ResponsiveRow:
    return ft.ResponsiveRow(
        spacing=12,
        run_spacing=12,
        controls=[
            _metric("Inicio", _format_datetime(forecast_start)),
            _metric("Final", _format_datetime(forecast_end)),
            _metric("Horizonte", f"{horizon} horas"),
            _metric("Input size", f"{input_size} horas"),
        ],
    )


def _metric(label: str, value: str) -> ft.Container:
    return ft.Container(
        col={"xs": 12, "sm": 6, "lg": 3},
        padding=12,
        border=_border("#CBD5E1"),
        border_radius=10,
        bgcolor="#FFFFFF",
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Text(label, size=11, color="#475569"),
                ft.Text(value or "-", size=13, weight=ft.FontWeight.W_600, color=PRIMARY_TEXT),
            ],
        ),
    )


def _forecast_chart(context_df: pd.DataFrame, forecast_df: pd.DataFrame) -> fc.LineChart:
    values = _combined_preview_values(context_df, forecast_df)
    min_y = float(values.min())
    max_y = float(values.max())
    y_padding = max((max_y - min_y) * 0.1, 1)
    context_points = _context_chart_points(context_df)
    forecast_points = _forecast_chart_points(forecast_df, len(context_points))
    forecast_series_points = _forecast_series_points(context_points, forecast_points)
    data_series = []

    if context_points:
        data_series.append(
            fc.LineChartData(
                points=context_points,
                color=CONTEXT_CHART_COLOR,
                stroke_width=2.5,
                curved=True,
                point=False,
                below_line_bgcolor="#DBEAFE",
            )
        )
    data_series.append(
        fc.LineChartData(
            points=forecast_series_points,
            color=FORECAST_CHART_COLOR,
            stroke_width=2.5,
            curved=True,
            dash_pattern=[6, 4],
            point=False,
            below_line_bgcolor="#FFEDD5",
        )
    )

    return fc.LineChart(
        data_series=data_series,
        min_x=0,
        max_x=max(len(context_points) + len(forecast_points) - 1, 1),
        min_y=min_y - y_padding,
        max_y=max_y + y_padding,
        left_axis=fc.ChartAxis(show_labels=False),
        bottom_axis=fc.ChartAxis(show_labels=False),
        horizontal_grid_lines=fc.ChartGridLines(color="#E2E8F0", interval=y_padding),
        vertical_grid_lines=fc.ChartGridLines(color="#F1F5F9", interval=6),
        height=150,
        expand=True,
    )


def _combined_preview_values(context_df: pd.DataFrame, forecast_df: pd.DataFrame) -> pd.Series:
    values = [forecast_df["yhat"]]
    if not context_df.empty:
        values.insert(0, context_df["y"])
    return pd.concat(values, ignore_index=True)


def _context_chart_points(df: pd.DataFrame) -> list[fc.LineChartDataPoint]:
    return [
        fc.LineChartDataPoint(x=index, y=float(row.y), tooltip=f"Contexto: {row.y:.2f}")
        for index, row in enumerate(df.itertuples())
    ]


def _forecast_chart_points(
    df: pd.DataFrame, x_offset: int
) -> list[fc.LineChartDataPoint]:
    return [
        fc.LineChartDataPoint(
            x=x_offset + index,
            y=float(row.yhat),
            tooltip=f"Forecast: {row.yhat:.2f}",
        )
        for index, row in enumerate(df.itertuples())
    ]


def _forecast_series_points(
    context_points: list[fc.LineChartDataPoint],
    forecast_points: list[fc.LineChartDataPoint],
) -> list[fc.LineChartDataPoint]:
    if not context_points:
        return forecast_points
    last_context_point = context_points[-1]
    connector = fc.LineChartDataPoint(
        x=last_context_point.x,
        y=last_context_point.y,
        point=False,
        show_tooltip=False,
    )
    return [connector, *forecast_points]


def _forecast_preview_legend(*, show_context: bool) -> ft.Row:
    controls: list[ft.Control] = []
    if show_context:
        controls.append(_legend_item(CONTEXT_CHART_COLOR, "Contexto"))
    controls.append(_legend_item(FORECAST_CHART_COLOR, "Pronostico", dashed=True))
    return ft.Row(spacing=12, controls=controls)


def _legend_item(color: str, label: str, *, dashed: bool = False) -> ft.Row:
    return ft.Row(
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            _legend_line(color, dashed=dashed),
            ft.Text(label, size=12, color=SECONDARY_TEXT),
        ],
    )


def _legend_line(color: str, *, dashed: bool) -> ft.Row | ft.Container:
    if not dashed:
        return ft.Container(width=20, height=3, border_radius=2, bgcolor=color)
    return ft.Row(
        spacing=3,
        controls=[
            ft.Container(width=7, height=3, border_radius=2, bgcolor=color),
            ft.Container(width=7, height=3, border_radius=2, bgcolor=color),
        ],
    )


def _format_datetime(value: Any) -> str:
    if not value:
        return "-"
    try:
        timestamp = pd.to_datetime(value, utc=True)
    except (TypeError, ValueError):
        return str(value)
    return timestamp.strftime("%Y-%m-%d %H:%M")


def _border(color: str) -> ft.Border:
    side = ft.BorderSide(1, color)
    return ft.Border(side, side, side, side)
