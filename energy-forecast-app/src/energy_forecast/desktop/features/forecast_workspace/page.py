from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import flet as ft

from energy_forecast.app_paths import AppPaths
from energy_forecast.desktop.background_operations import BackgroundOperations
from energy_forecast.desktop.layout import page_shell

from .components import (
    _context_section,
    _context_summary_content,
    _forecast_action_panel,
    _last_result_content,
    _model_details_dialog,
    _new_forecast_content,
    _page_header,
    _runs_content,
    _selected_source_summary,
    _source_group,
    _source_group_tabs,
    _source_list_content,
    _tab_label,
    _workspace_card,
)
from .constants import (
    PRIMARY_TEXT,
    SECONDARY_TEXT,
    SOURCE_GROUPS,
    SOURCE_LIST_HEIGHT,
    SOURCE_PAGE_SIZE,
    SOURCE_SCROLL_LOAD_THRESHOLD,
)
from .context import (
    _as_date,
    _build_context_summary,
    _configure_context_date_picker,
    _context_date_button_label,
    _context_date_label,
    _option_list,
    _prepare_context_date_state,
)
from .sources import (
    SourceInfo,
    _ensure_active_group,
    _import_source,
    _load_source_frame,
    _load_sources,
    _source_count_label,
    _source_group_title,
)


def build_forecast_workspace_page(
    page: ft.Page,
    paths: AppPaths,
    model: dict[str, object],
    background: BackgroundOperations | None = None,
) -> ft.Control:
    return page_shell(_workspace_content(page, paths, model, background))


def _workspace_content(
    page: ft.Page,
    paths: AppPaths,
    model: dict[str, object],
    background: BackgroundOperations | None,
) -> ft.Column:
    state: dict[str, Any] = {
        "sources": _load_sources(paths, model),
        "selected": None,
        "active_tab": "new",
        "active_group": "Modelo",
        "visible_counts": {group: SOURCE_PAGE_SIZE for group in SOURCE_GROUPS},
        "show_source_list": True,
        "source_frame": None,
        "context_mode": "last",
        "context_start_date": None,
        "context_start_hour": "",
        "context_hours_by_date": {},
        "context_summary": None,
        "forecasting": False,
        "last_result": None,
    }
    source_list = ft.Column(spacing=10, height=SOURCE_LIST_HEIGHT, scroll=ft.ScrollMode.AUTO)
    source_count = ft.Text(size=13, color=SECONDARY_TEXT)
    source_tabs = ft.Container()
    source_content = ft.Container()
    load_more_button = ft.TextButton("Cargar mas fuentes")
    tab_row = ft.Row(spacing=18)
    content_area = ft.Container()
    error = ft.Text("", size=13, color="#DC2626", visible=False)
    loading = ft.ProgressRing(width=18, height=18, visible=False)
    context_mode = ft.Dropdown(
        label="Modo de seleccion",
        value="last",
        color=PRIMARY_TEXT,
        border_color="#334155",
        focused_border_color=PRIMARY_TEXT,
        label_style=ft.TextStyle(color=PRIMARY_TEXT),
        text_style=ft.TextStyle(color=PRIMARY_TEXT),
        options=[
            ft.dropdown.Option("first", "Primeras filas disponibles"),
            ft.dropdown.Option("last", "Ultimas filas disponibles"),
            ft.dropdown.Option("from_timestamp", "Desde fecha y hora"),
        ],
    )
    context_date_picker = ft.DatePicker(
        confirm_text="Aplicar",
        cancel_text="Cancelar",
        help_text="Selecciona fecha inicial",
        entry_mode=ft.DatePickerEntryMode.CALENDAR,
    )
    context_date_summary = ft.Text("Selecciona una fuente.", size=13, color=PRIMARY_TEXT)
    context_hour = ft.Dropdown(
        label="Hora inicial",
        options=[],
        value="",
        width=180,
        color=PRIMARY_TEXT,
        border_color="#334155",
        focused_border_color=PRIMARY_TEXT,
        label_style=ft.TextStyle(color=PRIMARY_TEXT),
        text_style=ft.TextStyle(color=PRIMARY_TEXT),
    )
    context_date_button = ft.OutlinedButton(
        "Elegir fecha inicial",
        icon=ft.Icons.EVENT,
        icon_color=PRIMARY_TEXT,
        on_click=lambda event: open_context_date(event),
        style=ft.ButtonStyle(color=PRIMARY_TEXT),
    )
    context_datetime_controls = ft.Row(
        spacing=12,
        wrap=True,
        visible=False,
        controls=[context_date_button, context_hour],
    )
    context_summary = ft.Container()
    last_result_content = ft.Container()
    action_content = ft.Container()
    file_picker: ft.FilePicker | None = None

    def render_source_section() -> None:
        selected = state.get("selected")
        if selected is not None and not state["show_source_list"]:
            source_content.content = _selected_source_summary(selected, show_source_list)
            return

        _ensure_active_group(state)
        active_group = state["active_group"]
        group_sources = [item for item in state["sources"] if item.group == active_group]
        visible_count = state["visible_counts"][active_group]
        visible_sources = group_sources[:visible_count]
        source_tabs.content = _source_group_tabs(state, change_group)
        source_count.value = _source_count_label(len(visible_sources), len(group_sources))
        load_more_button.visible = len(visible_sources) < len(group_sources)
        source_list.controls = [
            _source_group(_source_group_title(active_group), visible_sources, selected, select_source)
        ]
        source_content.content = _source_list_content(
            source_tabs, source_count, source_list, load_more_button
        )

    def render_workspace() -> None:
        tab_row.controls = [
            _tab_label("Nuevo pronostico", state["active_tab"] == "new", set_tab("new")),
            _tab_label("Ejecuciones", state["active_tab"] == "runs", set_tab("runs")),
        ]
        content_area.content = (
            _new_forecast_content(
                model,
                source_content,
                _context_section(
                    model,
                    context_mode,
                    context_datetime_controls,
                    context_date_summary,
                    context_summary,
                ),
                error,
                open_import,
                last_result_content,
                action_content,
            )
            if state["active_tab"] == "new"
            else _runs_content(page, paths, model, on_deleted=refresh_runs_tab)
        )

    def set_tab(tab: str) -> ft.ControlEventHandler:
        def handler(_: ft.ControlEvent) -> None:
            state["active_tab"] = tab
            render_workspace()
            page.update()

        return handler

    def refresh_runs_tab(_: ft.ControlEvent | None = None) -> None:
        state["active_tab"] = "runs"
        render_workspace()
        page.update()

    def select_source(source: SourceInfo) -> None:
        try:
            frame = _load_source_frame(source.path)
        except Exception as exc:  # noqa: BLE001 - UI must surface source preview failures.
            show_error(str(exc))
            return
        state["selected"] = source
        state["source_frame"] = frame
        state["active_group"] = source.group
        state["show_source_list"] = False
        state["context_mode"] = "last"
        context_mode.value = "last"
        _prepare_context_date_state(state, frame)
        _configure_context_date_picker(context_date_picker, state)
        refresh_context_controls()
        error.visible = False
        render_source_section()
        page.update()

    def show_source_list(_: ft.ControlEvent) -> None:
        selected = state.get("selected")
        if selected is not None:
            state["active_group"] = selected.group
        state["show_source_list"] = True
        render_source_section()
        page.update()

    def refresh_context_controls() -> None:
        context_mode.value = state["context_mode"]
        available_hours = state.get("context_hours_by_date", {}).get(
            state.get("context_start_date"), []
        )
        context_hour.options = _option_list(available_hours)
        if context_hour.value not in available_hours:
            context_hour.value = available_hours[0] if available_hours else ""
        state["context_start_hour"] = context_hour.value or ""
        context_date_button.content = _context_date_button_label(state)
        context_datetime_controls.visible = state["context_mode"] == "from_timestamp"
        context_date_summary.visible = context_datetime_controls.visible
        context_date_summary.value = _context_date_label(state)
        state["context_summary"] = _build_context_summary(state, model)
        context_summary.content = _context_summary_content(state["context_summary"])
        refresh_action_content()

    def refresh_last_result() -> None:
        last_result_content.content = _last_result_content(state.get("last_result"))

    def refresh_action_content() -> None:
        background_running = (
            background is not None and background.has_running_operation()
        )
        disabled = (
            state["forecasting"]
            or background_running
            or not _context_ready(state.get("context_summary"))
        )
        loading.visible = state["forecasting"]
        action_content.content = _forecast_action_panel(generate_forecast, loading, disabled)

    def change_context_mode(_: ft.ControlEvent) -> None:
        state["context_mode"] = context_mode.value or "last"
        refresh_context_controls()
        page.update()

    def change_context_hour(_: ft.ControlEvent) -> None:
        state["context_start_hour"] = context_hour.value or ""
        refresh_context_controls()
        page.update()

    def open_context_date(_: ft.ControlEvent) -> None:
        if state.get("source_frame") is None:
            show_error("Selecciona una fuente antes de elegir fecha.")
            return
        page.show_dialog(context_date_picker)

    def change_context_date(event: ft.ControlEvent) -> None:
        selected_value = getattr(event.control, "value", None)
        if selected_value is not None:
            state["context_start_date"] = _as_date(selected_value)
        context_hour.value = ""
        refresh_context_controls()
        page.update()

    def change_group(group: str) -> None:
        state["active_group"] = group
        render_source_section()
        page.update()

    def load_more_sources() -> bool:
        active_group = state["active_group"]
        total = sum(1 for item in state["sources"] if item.group == active_group)
        current = state["visible_counts"][active_group]
        if current >= total:
            return False
        state["visible_counts"][active_group] = min(total, current + SOURCE_PAGE_SIZE)
        render_source_section()
        return True

    def on_source_scroll(event: Any) -> None:
        max_scroll = getattr(event, "max_scroll_extent", 0) or 0
        pixels = getattr(event, "pixels", 0) or 0
        if pixels >= max_scroll - SOURCE_SCROLL_LOAD_THRESHOLD and load_more_sources():
            page.update()

    def on_load_more_sources(_: ft.ControlEvent) -> None:
        if load_more_sources():
            page.update()

    def show_error(message: str) -> None:
        error.value = message
        error.visible = True
        page.update()

    def generate_forecast(_: ft.ControlEvent) -> None:
        summary = state.get("context_summary")
        selected = state.get("selected")
        if selected is None or not _context_ready(summary):
            show_error("Selecciona una fuente y un contexto valido antes de generar el pronostico.")
            return
        if background is not None and background.has_running_operation():
            show_error("Ya hay una tarea en segundo plano en curso. Espera a que termine antes de generar otro pronostico.")
            return
        state["forecasting"] = True
        error.visible = False
        refresh_action_content()
        if background is not None:
            background.show(
                "Pronostico en curso",
                "Generando forecast con el modelo seleccionado.",
                key="forecast",
            )
        page.update()

        async def run_forecast_task() -> None:
            try:
                await asyncio.sleep(0.1)
                result = await asyncio.to_thread(
                    _generate_forecast_sync,
                    paths,
                    model,
                    summary,
                    selected.name,
                )
            except Exception as exc:  # noqa: BLE001 - execution errors must be visible in the UI.
                state["forecasting"] = False
                refresh_action_content()
                message = str(exc)
                if background is not None:
                    background.finish(
                        "Pronostico en curso",
                        f"No se pudo generar el forecast: {message}",
                        success=False,
                        key="forecast",
                    )
                show_error(message)
                return
            state["forecasting"] = False
            state["last_result"] = _forecast_result_summary(result, selected.name, summary)
            refresh_last_result()
            refresh_action_content()
            if background is not None:
                background.finish(
                    "Pronostico generado",
                    "Forecast generado correctamente.",
                    success=True,
                    key="forecast",
                )
            page.update()

        page.run_task(run_forecast_task)

    def import_file(source: Path) -> None:
        try:
            imported_path = _import_source(source, paths)
        except Exception as exc:  # noqa: BLE001 - UI should surface import failures.
            show_error(str(exc))
            return
        state["sources"] = _load_sources(paths, model)
        state["selected"] = next(
            (item for item in state["sources"] if item.path == imported_path), None
        )
        state["active_group"] = "Importado"
        state["show_source_list"] = False
        error.visible = False
        if state["selected"] is not None:
            state["source_frame"] = _load_source_frame(imported_path)
            _prepare_context_date_state(state, state["source_frame"])
            _configure_context_date_picker(context_date_picker, state)
            refresh_context_controls()
        render_source_section()
        page.update()

    async def open_import(_: ft.ControlEvent) -> None:
        nonlocal file_picker
        if file_picker is None:
            file_picker = ft.FilePicker()
            page.services.append(file_picker)
            page.update()
        files = await file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["csv"],
            dialog_title="Importar CSV para pronostico",
        )
        if files:
            import_file(Path(files[0].path or ""))

    def show_details(_: ft.ControlEvent) -> None:
        page.show_dialog(_model_details_dialog(model))

    source_list.on_scroll = on_source_scroll
    load_more_button.on_click = on_load_more_sources
    context_mode.on_select = change_context_mode
    context_hour.on_select = change_context_hour
    context_date_picker.on_change = change_context_date
    refresh_context_controls()
    refresh_last_result()
    render_source_section()
    render_workspace()

    return ft.Column(
        spacing=18,
        controls=[
            _page_header(model, show_details),
            _workspace_card(tab_row, content_area),
        ],
    )


def _context_ready(summary: object) -> bool:
    return isinstance(summary, dict) and "context" in summary and "error" not in summary


def _generate_forecast_sync(
    paths: AppPaths,
    model: dict[str, object],
    summary: dict[str, object],
    dataset_name: str,
) -> object:
    from energy_forecast.services.forecasting import generate_nbeats_forecast

    return generate_nbeats_forecast(
        app_root=paths.workspace_root,
        model_path=str(model["model_dir"]),
        context=summary["context"],
        dataset_name=dataset_name,
    )


def _forecast_result_summary(
    result: object, dataset_name: str, context_summary: dict[str, object]
) -> dict[str, object]:
    forecast = result.forecast
    return {
        "run_id": result.run_id,
        "dataset": dataset_name,
        "last_input": context_summary["end"].strftime("%Y-%m-%d %H:%M"),
        "first_forecast": forecast["timestamp"].iloc[0].strftime("%Y-%m-%d %H:%M"),
    }
