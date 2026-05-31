import flet as ft

from energy_forecast.app_paths import AppPaths
from energy_forecast.desktop.features.model_selection.components.model_filters import (
    SelectionState,
    build_filter_button,
    build_filters_dialog,
    filter_models,
    update_filter_badge,
)
from energy_forecast.desktop.features.model_selection.components.model_list import build_model_list
from energy_forecast.desktop.layout import page_shell
from energy_forecast.desktop.navigation import navigate_to
from energy_forecast.storage.model_catalog import delete_pretrained_model, list_pretrained_models


def build_model_selection_page(
    page: ft.Page, state: SelectionState, paths: AppPaths
) -> ft.Control:
    models = list_pretrained_models(paths)
    model_list = ft.Column(spacing=12)
    result_count = ft.Text(size=13, color="#64748B")
    search = _search_field(state)
    refresh_button = _refresh_button()
    filter_button = build_filter_button()

    def refresh_models(event: ft.ControlEvent | None = None, *, reload: bool = False) -> None:
        nonlocal models
        if reload:
            models = list_pretrained_models(paths)
        state["query"] = search.value or ""
        filtered = filter_models(
            models=models,
            query=state["query"],
            zone=state.get("zone", ""),
            horizon=state.get("horizon", ""),
            input_size=state.get("input_size", ""),
            frequency=state.get("frequency", ""),
            max_steps=state.get("max_steps", ""),
        )

        model_list.controls = build_model_list(page, filtered, on_delete=confirm_delete_model)
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

    def confirm_delete_model(_: ft.ControlEvent, model: dict[str, object]) -> None:
        model_id = str(model["id"])
        title = str(model.get("title") or model.get("name") or model_id)

        def close_dialog(_: ft.ControlEvent | None = None) -> None:
            page.pop_dialog()

        def delete_model(_: ft.ControlEvent) -> None:
            try:
                delete_pretrained_model(model_id, paths)
            except Exception as exc:  # noqa: BLE001 - deletion errors should stay in UI.
                page.pop_dialog()
                page.snack_bar = ft.SnackBar(ft.Text(f"No se pudo borrar el modelo: {exc}"))
                page.snack_bar.open = True
                page.update()
                return
            page.pop_dialog()
            refresh_models(reload=True)
            page.update()

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Borrar modelo"),
                content=ft.Text(f"Esta accion eliminara permanentemente '{title}'."),
                actions=[
                    ft.TextButton("Cancelar", on_click=close_dialog),
                    ft.TextButton("Borrar", style=ft.ButtonStyle(color="#DC2626"), on_click=delete_model),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    search.on_change = refresh_models
    filter_button.on_click = open_filters
    refresh_button.on_click = lambda event: refresh_models(event, reload=True)

    refresh_models()

    return page_shell(
        ft.Column(
            spacing=18,
            controls=[
                _page_header(),
                _search_toolbar(search, refresh_button, filter_button),
                result_count,
                model_list,
            ],
        )
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


def _search_toolbar(search: ft.TextField, refresh_button: ft.IconButton, filter_button: ft.IconButton) -> ft.Row:
    return ft.Row(
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[search, refresh_button, filter_button],
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


def _refresh_button() -> ft.IconButton:
    return ft.IconButton(
        icon=ft.Icons.REFRESH,
        icon_color="#334155",
        tooltip="Recargar modelos",
    )


def build_create_model_button(page: ft.Page, disabled: bool = False) -> ft.FloatingActionButton:
    return ft.FloatingActionButton(
        content=ft.Icon(ft.Icons.ADD, color=ft.Colors.WHITE, size=24),
        bgcolor="#94A3B8" if disabled else "#0F172A",
        tooltip="Hay un entrenamiento en curso" if disabled else "Crear nuevo modelo",
        shape=ft.RoundedRectangleBorder(radius=14),
        on_click=None if disabled else lambda _: navigate_to(page, "/models/new"),
    )
