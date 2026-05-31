from __future__ import annotations

import flet as ft

from energy_forecast.desktop.features.forecast_workspace.constants import (
    PRIMARY_TEXT,
    SECONDARY_TEXT,
)


def _model_details_dialog(model: dict[str, object]) -> ft.AlertDialog:
    def close(event: ft.ControlEvent) -> None:
        event.page.pop_dialog()

    return ft.AlertDialog(
        modal=False,
        title=ft.Text("Detalles del modelo", color=PRIMARY_TEXT),
        content=ft.Container(width=360, content=_model_details_content(model)),
        actions=[ft.TextButton("Cerrar", on_click=close)],
    )


def _model_details_content(model: dict[str, object]) -> ft.Column:
    metadata = model.get("metadata")
    description = str(model.get("description") or "")
    if isinstance(metadata, dict):
        description = str(metadata.get("description") or description)
    controls = [
        _detail_item("Nombre", str(model["name"])),
        _detail_item("Dataset", str(model["dataset"])),
        _detail_item("Zona", str(model["zone"])),
        _detail_item("Tipo", str(model["model_type"]).upper()),
        _detail_item("Input size", str(model["input_size"])),
        _detail_item("Horizonte", str(model["horizon"])),
        _detail_item("Frecuencia", _frequency_label(str(model["frequency"]))),
        _detail_item("Max steps", str(model["max_steps"])),
    ]
    if description:
        controls.append(_detail_item("Descripcion", description))
    return ft.Column(spacing=12, controls=controls)


def _detail_item(label: str, value: str) -> ft.Container:
    return ft.Container(
        padding=ft.Padding(0, 0, 0, 10),
        content=ft.Column(
            spacing=3,
            controls=[
                ft.Text(label, size=12, color=SECONDARY_TEXT),
                ft.Text(value or "-", size=14, weight=ft.FontWeight.W_600, color=PRIMARY_TEXT),
            ],
        ),
    )


def _frequency_label(value: str) -> str:
    labels = {
        "h": "Horaria",
        "H": "Horaria",
        "D": "Diaria",
        "W": "Semanal",
        "MS": "Mensual",
    }
    label = labels.get(value, value or "-")
    return f"{label} ({value})" if value and label != value else label
