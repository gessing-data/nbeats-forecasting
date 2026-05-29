from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import flet as ft

from energy_forecast.app_paths import AppPaths
from energy_forecast.desktop.components.incremental_selector import (
    incremental_selector_content,
    incremental_selector_group,
    incremental_selector_tabs,
)
from energy_forecast.desktop.layout import page_shell
from energy_forecast.storage import safe_artifact_name


BORDER_COLOR = "#E2E8F0"
PRIMARY_TEXT = "#0F172A"
SECONDARY_TEXT = "#64748B"
SOURCE_GROUPS = ("Modelo", "Importado", "Procesado")
SOURCE_PAGE_SIZE = 6
SOURCE_LIST_HEIGHT = 360
SOURCE_SCROLL_LOAD_THRESHOLD = 80


@dataclass(frozen=True)
class SourceInfo:
    name: str
    path: Path
    group: str


def build_forecast_workspace_page(
    page: ft.Page,
    paths: AppPaths,
    model: dict[str, object],
) -> ft.Control:
    return page_shell(_workspace_content(page, paths, model))


def _workspace_content(page: ft.Page, paths: AppPaths, model: dict[str, object]) -> ft.Column:
    state: dict[str, Any] = {
        "sources": _load_sources(paths, model),
        "selected": None,
        "active_tab": "new",
        "active_group": "Modelo",
        "visible_counts": {group: SOURCE_PAGE_SIZE for group in SOURCE_GROUPS},
        "show_source_list": True,
    }
    source_list = ft.Column(spacing=10, height=SOURCE_LIST_HEIGHT, scroll=ft.ScrollMode.AUTO)
    source_count = ft.Text(size=13, color=SECONDARY_TEXT)
    source_tabs = ft.Container()
    source_content = ft.Container()
    load_more_button = ft.TextButton("Cargar mas fuentes")
    tab_row = ft.Row(spacing=18)
    content_area = ft.Container()
    error = ft.Text("", size=13, color="#DC2626", visible=False)
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
            _new_forecast_content(model, source_content, error, open_import)
            if state["active_tab"] == "new"
            else _runs_content()
        )

    def set_tab(tab: str) -> ft.ControlEventHandler:
        def handler(_: ft.ControlEvent) -> None:
            state["active_tab"] = tab
            render_workspace()
            page.update()

        return handler

    def select_source(source: SourceInfo) -> None:
        state["selected"] = source
        state["active_group"] = source.group
        state["show_source_list"] = False
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
    render_source_section()
    render_workspace()

    return ft.Column(
        spacing=18,
        controls=[
            _page_header(model, show_details),
            _workspace_card(tab_row, content_area),
        ],
    )


def _page_header(model: dict[str, object], on_details: ft.ControlEventHandler) -> ft.Row:
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
        spacing=12,
        controls=[
            ft.Column(
                spacing=8,
                expand=True,
                controls=[
                    ft.Text("Workspace de pronostico", size=28, weight=ft.FontWeight.W_600, color=PRIMARY_TEXT),
                    ft.Text(
                        f"Modelo seleccionado: {model['name']}. Elige la fuente que alimentara el pronostico.",
                        size=14,
                        color=SECONDARY_TEXT,
                    ),
                ],
            ),
            ft.OutlinedButton("Detalles del modelo", icon=ft.Icons.INFO_OUTLINE, on_click=on_details),
        ],
    )


def _workspace_card(tab_row: ft.Row, content_area: ft.Container) -> ft.Container:
    return _card(
        ft.Column(
            spacing=18,
            controls=[
                ft.Column(spacing=10, controls=[tab_row, ft.Container(height=1, bgcolor=BORDER_COLOR)]),
                content_area,
            ],
        )
    )


def _tab_label(label: str, active: bool, on_click: ft.ControlEventHandler) -> ft.Container:
    return ft.Container(
        padding=ft.Padding(0, 0, 0, 8),
        border=ft.Border(bottom=ft.BorderSide(2, PRIMARY_TEXT if active else ft.Colors.TRANSPARENT)),
        ink=True,
        on_click=on_click,
        content=ft.Text(
            label,
            size=14,
            weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_500,
            color=PRIMARY_TEXT if active else SECONDARY_TEXT,
        ),
    )


def _new_forecast_content(
    model: dict[str, object],
    source_content: ft.Container,
    error: ft.Text,
    on_import: ft.ControlEventHandler,
) -> ft.Column:
    return ft.Column(
        spacing=18,
        controls=[
            _last_result_card(),
            _source_section(source_content, on_import),
            _context_placeholder(model),
            error,
            _forecast_action_placeholder(),
        ],
    )


def _runs_content() -> ft.Column:
    return ft.Column(spacing=18, controls=[_runs_empty_state()])


def _last_result_card() -> ft.Container:
    return _section_card(
        icon=ft.Icons.INSIGHTS,
        title="Ultimo resultado",
        body="Aun no hay ejecuciones para este modelo. Cuando generes el primer pronostico, su resumen aparecera aqui.",
    )


def _source_section(source_content: ft.Container, on_import: ft.ControlEventHandler) -> ft.Container:
    return _section_card(
        icon=ft.Icons.SOURCE,
        title="Fuente del pronostico",
        body="Selecciona la fuente que alimentara el contexto. La validacion se ejecutara al generar el pronostico.",
        extra=[
            ft.Row(
                alignment=ft.MainAxisAlignment.END,
                controls=[ft.OutlinedButton("Importar CSV nuevo", icon=ft.Icons.UPLOAD_FILE, on_click=on_import)],
            ),
            source_content,
        ],
    )


def _source_list_content(
    source_tabs: ft.Container,
    source_count: ft.Text,
    source_list: ft.Column,
    load_more_button: ft.TextButton,
) -> ft.Column:
    return incremental_selector_content(
        source_tabs, source_count, source_list, load_more_button
    )


def _source_group_tabs(state: dict[str, Any], on_change: Any) -> ft.Control:
    groups = _available_groups(state)
    return incremental_selector_tabs(
        groups, state["active_group"], _source_group_title, on_change
    )


def _source_group(title: str, sources: list[SourceInfo], selected: SourceInfo | None, on_select: Any) -> ft.Column:
    return incremental_selector_group(
        title,
        sources,
        "No hay fuentes disponibles.",
        lambda item: _source_card(item, selected, on_select),
    )


def _source_card(source: SourceInfo, selected: SourceInfo | None, on_select: Any) -> ft.Container:
    is_selected = selected is not None and selected.path == source.path
    return ft.Container(
        width=float("inf"),
        padding=14,
        border=_border("#334155" if is_selected else BORDER_COLOR),
        border_radius=12,
        bgcolor="#F8FAFC" if is_selected else ft.Colors.WHITE,
        ink=True,
        on_click=lambda _: on_select(source),
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Text(source.name, size=15, weight=ft.FontWeight.W_600, color=PRIMARY_TEXT),
                ft.Text(f"{source.group} | {source.path.name}", size=12, color=SECONDARY_TEXT),
                ft.Text("Sin validar", size=12, color=SECONDARY_TEXT),
            ],
        ),
    )


def _selected_source_summary(source: SourceInfo, on_change: ft.ControlEventHandler) -> ft.Container:
    return ft.Container(
        width=float("inf"),
        border=_border("#334155"),
        border_radius=12,
        bgcolor="#F8FAFC",
        padding=14,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=6,
                    expand=True,
                    controls=[
                        ft.Text("Fuente seleccionada", size=13, weight=ft.FontWeight.W_600, color=SECONDARY_TEXT),
                        ft.Text(source.name, size=16, weight=ft.FontWeight.W_600, color=PRIMARY_TEXT),
                        ft.Text(f"{source.group} | {source.path.name}", size=12, color=SECONDARY_TEXT),
                        ft.Text("Se validara al generar el pronostico.", size=12, color=SECONDARY_TEXT),
                    ],
                ),
                ft.OutlinedButton("Cambiar fuente", icon=ft.Icons.SWAP_HORIZ, on_click=on_change),
            ],
        ),
    )


def _context_placeholder(model: dict[str, object]) -> ft.Container:
    return _section_card(
        icon=ft.Icons.DATE_RANGE,
        title="Seleccion temporal",
        body="La seleccion temporal usara min_date y max_date una vez se conecte la ejecucion del pronostico.",
        footer=f"Contexto requerido: {model['input_size']} filas",
    )


def _forecast_action_placeholder() -> ft.Container:
    return ft.Container(
        width=float("inf"),
        padding=16,
        border=_border("#CBD5E1"),
        border_radius=14,
        bgcolor="#F8FAFC",
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            wrap=True,
            spacing=12,
            run_spacing=8,
            controls=[
                ft.Text("La ejecucion real validara fuente y contexto antes de pronosticar.", size=13, color=SECONDARY_TEXT),
                ft.FilledButton("Generar pronostico", disabled=True),
            ],
        ),
    )


def _runs_empty_state() -> ft.Container:
    return ft.Container(
        width=float("inf"),
        padding=16,
        border=_border("#CBD5E1"),
        border_radius=12,
        bgcolor="#F8FAFC",
        content=ft.Text("Ejecuciones: no hay pronosticos guardados para este modelo.", size=13, color=SECONDARY_TEXT),
    )


def _load_sources(paths: AppPaths, model: dict[str, object]) -> list[SourceInfo]:
    sources: list[SourceInfo] = []
    training_source = _training_source_path(paths, model)
    if training_source is not None:
        sources.append(_source_info(training_source, "Modelo"))
    sources.extend(_directory_sources(paths.imported_data_dir, "Importado"))
    sources.extend(_directory_sources(paths.processed_data_dir, "Procesado"))
    return sources


def _directory_sources(directory: Path, group: str) -> list[SourceInfo]:
    if not directory.exists():
        return []
    paths = sorted(directory.glob("*.csv"))
    if group == "Importado":
        paths = [path for path in paths if not _is_generated_artifact(path)]
    return [_source_info(path, group) for path in paths]


def _is_generated_artifact(path: Path) -> bool:
    return path.name.endswith(("_training_input.csv", "_forecast_input.csv"))


def _training_source_path(paths: AppPaths, model: dict[str, object]) -> Path | None:
    metadata = model.get("metadata")
    if not isinstance(metadata, dict):
        return None
    source_file = metadata.get("source_file")
    if isinstance(source_file, str) and source_file:
        candidate = Path(source_file)
        if candidate.exists() and _is_under(candidate, paths.data_dir):
            return candidate
    return None


def _source_info(path: Path, group: str) -> SourceInfo:
    return SourceInfo(path.stem, path, group)


def _import_source(source: Path, paths: AppPaths) -> Path:
    if not source.exists():
        raise ValueError("El archivo seleccionado no existe.")
    paths.imported_data_dir.mkdir(parents=True, exist_ok=True)
    target = paths.imported_data_dir / f"{safe_artifact_name(source.stem)}.csv"
    counter = 2
    while target.exists():
        target = paths.imported_data_dir / f"{safe_artifact_name(source.stem)}-{counter}.csv"
        counter += 1
    shutil.copy2(source, target)
    return target


def _available_groups(state: dict[str, Any]) -> list[str]:
    return [group for group in SOURCE_GROUPS if any(item.group == group for item in state["sources"])] or ["Procesado"]


def _ensure_active_group(state: dict[str, Any]) -> None:
    groups = _available_groups(state)
    if state["active_group"] not in groups:
        state["active_group"] = groups[0]


def _source_group_title(group: str) -> str:
    labels = {"Modelo": "Fuente del modelo", "Importado": "CSV importados", "Procesado": "Datasets procesados"}
    return labels.get(group, group)


def _source_count_label(visible: int, total: int) -> str:
    if total == 0:
        return "No hay fuentes disponibles."
    if visible >= total:
        return f"Mostrando {total} fuente{'s' if total != 1 else ''}."
    return f"Mostrando {visible} de {total} fuentes. Desplazate para cargar mas."


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


def _section_card(
    *,
    icon: str,
    title: str,
    body: str,
    footer: str | None = None,
    extra: list[ft.Control] | None = None,
) -> ft.Container:
    controls: list[ft.Control] = [
        ft.Row(spacing=10, controls=[ft.Icon(icon, size=20, color=SECONDARY_TEXT), ft.Text(title, size=17, weight=ft.FontWeight.W_600, color=PRIMARY_TEXT)]),
        ft.Text(body, size=13, color=SECONDARY_TEXT),
    ]
    if footer:
        controls.append(ft.Text(footer, size=12, color="#475569", weight=ft.FontWeight.W_500))
    controls.extend(extra or [])
    return ft.Container(
        width=float("inf"),
        padding=16,
        border=_border(BORDER_COLOR),
        border_radius=14,
        bgcolor=ft.Colors.WHITE,
        content=ft.Column(spacing=10, controls=controls),
    )


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
    labels = {"h": "Horaria", "H": "Horaria", "D": "Diaria", "W": "Semanal", "MS": "Mensual"}
    label = labels.get(value, value or "-")
    return f"{label} ({value})" if value and label != value else label


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _card(content: ft.Control) -> ft.Container:
    return ft.Container(
        width=float("inf"),
        padding=18,
        bgcolor=ft.Colors.WHITE,
        border=_border(BORDER_COLOR),
        border_radius=16,
        content=content,
    )


def _border(color: str) -> ft.Border:
    side = ft.BorderSide(1, color)
    return ft.Border(side, side, side, side)
