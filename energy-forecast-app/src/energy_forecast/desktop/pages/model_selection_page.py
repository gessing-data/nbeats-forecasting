import flet as ft

from energy_forecast.desktop.components.model_filters import (
    SelectionState,
    build_filter_button,
    build_filters_dialog,
    filter_models,
    update_filter_badge,
)
from energy_forecast.desktop.components.model_list import build_model_list
from energy_forecast.desktop.model_catalog import list_pretrained_models


BACKGROUND_COLOR = "#F8FAFC"
MAX_CONTENT_WIDTH = 920
PAGE_PADDING = 24


def build_model_selection_page(page: ft.Page, state: SelectionState) -> ft.Control:
    models = list_pretrained_models()
    model_list = ft.Column(spacing=12)
    result_count = ft.Text(size=13, color="#64748B")
    search = _search_field(state)
    filter_button = build_filter_button()

    def refresh_models(event: ft.ControlEvent | None = None) -> None:
        state["query"] = search.value or ""
        filtered = filter_models(
            models=models,
            query=state["query"],
            country=state.get("country", ""),
            horizon=state.get("horizon", ""),
            input_size=state.get("input_size", ""),
            frequency=state.get("frequency", ""),
            max_steps=state.get("max_steps", ""),
        )

        model_list.controls = build_model_list(page, filtered)
        result_count.value = f"{len(filtered)} modelo{'s' if len(filtered) != 1 else ''} disponible{'s' if len(filtered) != 1 else ''}"
        update_filter_badge(filter_button, state)
        if event is not None:
            page.update()

    def open_filters(_: ft.ControlEvent) -> None:
        page.show_dialog(
            build_filters_dialog(
                page=page,
                models=models,
                state=state,
                on_apply=refresh_models,
                on_clear=refresh_models,
            )
        )

    search.on_change = refresh_models
    filter_button.on_click = open_filters

    refresh_models()

    return _page_shell(
        ft.Column(
            spacing=18,
            controls=[
                _page_header(),
                _search_toolbar(search, filter_button),
                result_count,
                model_list,
            ],
        )
    )


def _page_shell(content: ft.Control) -> ft.Container:
    return ft.Container(
        expand=True,
        bgcolor=BACKGROUND_COLOR,
        alignment=ft.Alignment(0, -1),
        content=ft.Container(
            width=MAX_CONTENT_WIDTH + (PAGE_PADDING * 2),
            padding=ft.Padding(PAGE_PADDING, 28, PAGE_PADDING, 28),
            content=content,
        ),
    )


def _page_header() -> ft.Column:
    return ft.Column(
        spacing=8,
        controls=[
            ft.Text(
                "Selecciona un modelo N-BEATS preentrenado",
                size=28,
                weight=ft.FontWeight.W_600,
                color="#0F172A",
            ),
            ft.Text(
                "Cada modelo representa una configuracion entrenada para una serie de demanda electrica.",
                size=14,
                color="#64748B",
            ),
        ],
    )


def _search_toolbar(search: ft.TextField, filter_button: ft.IconButton) -> ft.Row:
    return ft.Row(
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[search, filter_button],
    )


def _search_field(state: SelectionState) -> ft.TextField:
    return ft.TextField(
        label="Buscar",
        hint_text="Modelo, pais o codigo",
        prefix_icon=ft.Icons.SEARCH,
        border_color="#CBD5E1",
        focused_border_color="#334155",
        value=state.get("query", ""),
        expand=True,
    )


def build_create_model_button() -> ft.FloatingActionButton:
    return ft.FloatingActionButton(
        content=ft.Icon(ft.Icons.ADD, color=ft.Colors.WHITE, size=24),
        bgcolor="#0F172A",
        tooltip="Crear nuevo modelo",
        shape=ft.RoundedRectangleBorder(radius=14),
        on_click=lambda _: None,
    )
