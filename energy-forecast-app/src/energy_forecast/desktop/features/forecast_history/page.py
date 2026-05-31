from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import flet as ft
import pandas as pd

from energy_forecast.app_paths import AppPaths
from energy_forecast.desktop.components.forecast_preview_card import forecast_preview_card
from energy_forecast.desktop.layout import page_shell
from energy_forecast.desktop.navigation import navigate_to
from energy_forecast.storage.model_catalog import list_pretrained_models


BORDER_COLOR = "#E2E8F0"
PRIMARY_TEXT = "#0F172A"
SECONDARY_TEXT = "#64748B"
PREVIEW_ROWS = 24
CONTEXT_PREVIEW_ROWS = 24


@dataclass(frozen=True)
class ForecastRun:
    run_id: str
    model_id: str
    model_name: str
    dataset: str
    generated_at: str
    horizon: int
    input_size: int
    forecast_rows: int
    first_forecast_timestamp: str
    last_forecast_timestamp: str
    forecast_path: Path
    forecast_input_path: Path | None
    metadata_path: Path
    metadata: dict[str, Any]
    preview: pd.DataFrame
    context_preview: pd.DataFrame


def build_forecast_history_page(page: ft.Page, paths: AppPaths) -> ft.Control:
    runs = _list_forecast_runs(paths)
    return page_shell(
        ft.Column(
            spacing=18,
            controls=[
                _page_header(),
                _result_count(runs),
                _run_list(page, runs),
            ],
        )
    )


def _list_forecast_runs(paths: AppPaths) -> list[ForecastRun]:
    models_by_id = {str(model["id"]): model for model in list_pretrained_models(paths)}
    if not paths.models_dir.exists():
        return []

    runs: list[ForecastRun] = []
    for metadata_path in sorted(paths.models_dir.glob("*/runs/*/metadata.json")):
        metadata = _read_json(metadata_path)
        if metadata is None:
            continue
        run = _forecast_run_from_metadata(metadata_path, metadata, models_by_id)
        if run is not None:
            runs.append(run)

    return sorted(runs, key=lambda run: run.generated_at, reverse=True)


def _forecast_run_from_metadata(
    metadata_path: Path,
    metadata: dict[str, Any],
    models_by_id: dict[str, dict[str, object]],
) -> ForecastRun | None:
    model_id = str(metadata.get("model_id") or metadata_path.parents[2].name)
    run_id = str(metadata.get("run_id") or metadata_path.parent.name)
    forecast_path = Path(str(metadata.get("forecast_path") or metadata_path.parent / "forecast.csv"))
    if not forecast_path.exists():
        return None

    preview = _read_forecast_preview(forecast_path)
    forecast_input_path = _optional_path(metadata.get("forecast_input_path"))
    context_preview = _read_context_preview(forecast_input_path)
    model = models_by_id.get(model_id, {})
    return ForecastRun(
        run_id=run_id,
        model_id=model_id,
        model_name=str(model.get("name") or metadata.get("model") or model_id),
        dataset=str(metadata.get("dataset") or model.get("dataset") or "Dataset"),
        generated_at=str(metadata.get("generated_at") or ""),
        horizon=_safe_int(metadata.get("horizon")),
        input_size=_safe_int(metadata.get("input_size")),
        forecast_rows=_safe_int(metadata.get("forecast_rows"), len(preview)),
        first_forecast_timestamp=_first_forecast_timestamp(preview, metadata),
        last_forecast_timestamp=_last_forecast_timestamp(preview, metadata),
        forecast_path=forecast_path,
        forecast_input_path=forecast_input_path,
        metadata_path=metadata_path,
        metadata=metadata,
        preview=preview,
        context_preview=context_preview,
    )


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _read_forecast_preview(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, nrows=PREVIEW_ROWS)
    except OSError:
        return pd.DataFrame(columns=["timestamp", "yhat"])
    if "timestamp" not in df.columns or "yhat" not in df.columns:
        return pd.DataFrame(columns=["timestamp", "yhat"])
    preview = df.loc[:, ["timestamp", "yhat"]].copy()
    preview["timestamp"] = pd.to_datetime(preview["timestamp"], errors="coerce", utc=True)
    preview["yhat"] = pd.to_numeric(preview["yhat"], errors="coerce")
    return preview.dropna(subset=["timestamp", "yhat"]).reset_index(drop=True)


def _read_context_preview(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame(columns=["timestamp", "y"])
    try:
        df = pd.read_csv(path)
    except OSError:
        return pd.DataFrame(columns=["timestamp", "y"])
    if "timestamp" not in df.columns or "y" not in df.columns:
        return pd.DataFrame(columns=["timestamp", "y"])
    preview = df.loc[:, ["timestamp", "y"]].copy()
    preview["timestamp"] = pd.to_datetime(preview["timestamp"], errors="coerce", utc=True)
    preview["y"] = pd.to_numeric(preview["y"], errors="coerce")
    preview = preview.dropna(subset=["timestamp", "y"]).reset_index(drop=True)
    return preview.tail(CONTEXT_PREVIEW_ROWS).reset_index(drop=True)


def _optional_path(value: Any) -> Path | None:
    if not value:
        return None
    return Path(str(value))


def _first_forecast_timestamp(preview: pd.DataFrame, metadata: dict[str, Any]) -> str:
    metadata_value = metadata.get("first_forecast_timestamp")
    if metadata_value:
        return str(metadata_value)
    if not preview.empty:
        return preview["timestamp"].iloc[0].isoformat()
    return ""


def _last_forecast_timestamp(preview: pd.DataFrame, metadata: dict[str, Any]) -> str:
    metadata_value = metadata.get("last_forecast_timestamp")
    if metadata_value:
        return str(metadata_value)
    if not preview.empty:
        return preview["timestamp"].iloc[-1].isoformat()
    return ""


def _page_header() -> ft.Column:
    return ft.Column(
        spacing=8,
        controls=[
            ft.Text(
                "Historial de forecasts",
                size=28,
                weight=ft.FontWeight.W_600,
                color=PRIMARY_TEXT,
            ),
            ft.Text(
                "Consulta las ejecuciones de forecast generadas por los modelos entrenados.",
                size=14,
                color=SECONDARY_TEXT,
            ),
        ],
    )


def _result_count(runs: list[ForecastRun]) -> ft.Text:
    total = len(runs)
    label = "forecast disponible" if total == 1 else "forecasts disponibles"
    return ft.Text(f"{total} {label}", size=13, color=SECONDARY_TEXT)


def _run_list(page: ft.Page, runs: list[ForecastRun]) -> ft.Control:
    if not runs:
        return _empty_state()
    return ft.Column(
        spacing=12,
        controls=[_forecast_card(page, run) for run in runs],
    )


def _empty_state() -> ft.Container:
    return _card(
        ft.Column(
            spacing=8,
            controls=[
                ft.Text(
                    "Todavia no hay forecasts generados.",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=PRIMARY_TEXT,
                ),
                ft.Text(
                    "Cuando ejecutes forecasts desde un modelo, sus resultados apareceran aqui.",
                    size=13,
                    color=SECONDARY_TEXT,
                ),
            ],
        )
    )


def _forecast_card(
    page: ft.Page, run: ForecastRun, *, show_model_button: bool = True
) -> ft.Container:
    return _card(
        ft.Column(
            spacing=14,
            controls=[
                _forecast_card_header(run),
                _forecast_preview(run),
                _forecast_card_actions(page, run, show_model_button=show_model_button),
            ],
        )
    )


def _forecast_card_actions(
    page: ft.Page, run: ForecastRun, *, show_model_button: bool
) -> ft.Row:
    controls: list[ft.Control] = [
        ft.OutlinedButton(
            "Ver detalles",
            icon=ft.Icons.INFO_OUTLINE,
            on_click=lambda _: _show_run_details(page, run),
        )
    ]
    if show_model_button:
        controls.append(
            ft.FilledButton(
                "Ir al modelo",
                icon=ft.Icons.ARROW_FORWARD,
                on_click=lambda _: navigate_to(page, f"/models/{run.model_id}"),
            )
        )
    return ft.Row(alignment=ft.MainAxisAlignment.END, controls=controls)


def _forecast_card_header(run: ForecastRun) -> ft.Row:
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Column(
                spacing=4,
                expand=True,
                controls=[
                    ft.Text(
                        f"Forecast {run.dataset}",
                        size=18,
                        weight=ft.FontWeight.W_600,
                        color=PRIMARY_TEXT,
                    ),
                    ft.Text(run.model_name, size=13, color=SECONDARY_TEXT),
                ],
            ),
            ft.Text(_format_datetime(run.generated_at), size=12, color=SECONDARY_TEXT),
        ],
    )


def _forecast_preview(run: ForecastRun) -> ft.Control:
    return forecast_preview_card(
        context_df=run.context_preview,
        forecast_df=run.preview,
        forecast_start=run.first_forecast_timestamp,
        forecast_end=run.last_forecast_timestamp,
        horizon=run.horizon,
        input_size=run.input_size,
    )


def _show_run_details(page: ft.Page, run: ForecastRun) -> None:
    details = [
        ("Run ID", run.run_id),
        ("Modelo", run.model_name),
        ("Model ID", run.model_id),
        ("Dataset", run.dataset),
        ("Generado", _format_datetime(run.generated_at)),
        ("Input size", f"{run.input_size} horas"),
        ("Fin forecast", _format_datetime(run.last_forecast_timestamp)),
        ("Forecast input path", str(run.forecast_input_path or "-")),
        ("Forecast path", str(run.forecast_path)),
        ("Metadata path", str(run.metadata_path)),
    ]
    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text("Detalles del forecast"),
            content=ft.Column(
                tight=True,
                spacing=8,
                controls=[_detail_row(label, value) for label, value in details],
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: page.pop_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    )


def _detail_row(label: str, value: str) -> ft.Control:
    return ft.Column(
        spacing=2,
        controls=[
            ft.Text(label, size=11, color=SECONDARY_TEXT),
            ft.Text(value or "-", size=13, color=PRIMARY_TEXT, selectable=True),
        ],
    )


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _format_datetime(value: str) -> str:
    if not value:
        return "-"
    try:
        timestamp = pd.to_datetime(value, utc=True)
    except (TypeError, ValueError):
        return value
    return timestamp.strftime("%Y-%m-%d %H:%M UTC")


def _card(content: ft.Control) -> ft.Container:
    return ft.Container(
        width=float("inf"),
        bgcolor=ft.Colors.WHITE,
        border=_border(BORDER_COLOR),
        border_radius=16,
        padding=18,
        content=content,
    )


def _border(color: str) -> ft.Border:
    side = ft.BorderSide(1, color)
    return ft.Border(side, side, side, side)
