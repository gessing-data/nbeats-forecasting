import flet as ft

from energy_forecast.desktop.features.model_selection.components.model_card import model_card
from energy_forecast.desktop.navigation import navigate_to
from energy_forecast.storage.model_catalog import ModelRecord


def build_model_list(
    page: ft.Page,
    models: list[ModelRecord],
    on_delete: ft.EventHandler | None = None,
) -> list[ft.Control]:
    if not models:
        return [_empty_state()]

    return [
        model_card(
            name=str(model["name"]),
            zone=str(model["zone"]),
            zone_code=str(model["zone_code"]),
            description=str(model["description"]),
            input_size=int(model["input_size"]),
            horizon=int(model["horizon"]),
            frequency=str(model["frequency"]),
            max_steps=int(model["max_steps"]),
            on_click=lambda _, model_id=model["id"]: navigate_to(
                page, f"/models/{model_id}"
            ),
            on_delete=lambda event, model=model: on_delete(event, model) if on_delete is not None else None,
        )
        for model in models
    ]


def _empty_state() -> ft.Container:
    return ft.Container(
        padding=24,
        border=_border("#E2E8F0"),
        border_radius=14,
        bgcolor=ft.Colors.WHITE,
        content=ft.Text("No se encontraron modelos con esos filtros.", color="#64748B"),
    )


def _border(color: str) -> ft.Border:
    side = ft.BorderSide(1, color)
    return ft.Border(side, side, side, side)
