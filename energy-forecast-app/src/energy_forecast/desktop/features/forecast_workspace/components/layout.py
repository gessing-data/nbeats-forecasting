from __future__ import annotations

import flet as ft

from energy_forecast.app_paths import AppPaths
from energy_forecast.desktop.features.forecast_history.page import (
    _forecast_card,
    _list_forecast_runs,
)
from energy_forecast.desktop.features.forecast_workspace.components.common import (
    _card,
    _section_card,
)
from energy_forecast.desktop.features.forecast_workspace.constants import (
    BORDER_COLOR,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
)
from energy_forecast.desktop.features.forecast_workspace.utils import _border


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
                    ft.Text(
                        "Workspace de pronostico",
                        size=28,
                        weight=ft.FontWeight.W_600,
                        color=PRIMARY_TEXT,
                    ),
                    ft.Text(
                        f"Modelo seleccionado: {model['name']}. Elige la fuente que alimentara el pronostico.",
                        size=14,
                        color=SECONDARY_TEXT,
                    ),
                ],
            ),
            ft.OutlinedButton(
                "Detalles del modelo", icon=ft.Icons.INFO_OUTLINE, on_click=on_details
            ),
        ],
    )


def _workspace_card(tab_row: ft.Row, content_area: ft.Container) -> ft.Container:
    return _card(
        ft.Column(
            spacing=18,
            controls=[
                ft.Column(
                    spacing=10,
                    controls=[tab_row, ft.Container(height=1, bgcolor=BORDER_COLOR)],
                ),
                content_area,
            ],
        )
    )


def _tab_label(label: str, active: bool, on_click: ft.ControlEventHandler) -> ft.Container:
    return ft.Container(
        padding=ft.Padding(0, 0, 0, 8),
        border=ft.Border(
            bottom=ft.BorderSide(2, PRIMARY_TEXT if active else ft.Colors.TRANSPARENT)
        ),
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
    context_content: ft.Container,
    error: ft.Text,
    on_import: ft.ControlEventHandler,
    last_result: ft.Container,
    action_content: ft.Container,
) -> ft.Column:
    return ft.Column(
        spacing=18,
        controls=[
            last_result,
            _source_section(source_content, on_import),
            context_content,
            error,
            action_content,
        ],
    )


def _runs_content(
    page: ft.Page,
    paths: AppPaths,
    model: dict[str, object],
    on_deleted: ft.ControlEventHandler | None = None,
) -> ft.Column:
    model_id = str(model["id"])
    runs = [run for run in _list_forecast_runs(paths) if run.model_id == model_id]
    if not runs:
        return ft.Column(spacing=18, controls=[_runs_empty_state()])
    return ft.Column(
        spacing=12,
        controls=[
            _forecast_card(
                page,
                run,
                show_model_button=False,
                on_deleted=on_deleted,
            )
            for run in runs
        ],
    )


def _last_result_card() -> ft.Container:
    return _section_card(
        icon=ft.Icons.INSIGHTS,
        title="Ultimo resultado",
        body="Aun no hay ejecuciones para este modelo. Cuando generes el primer pronostico, su resumen aparecera aqui.",
    )


def _source_section(
    source_content: ft.Container, on_import: ft.ControlEventHandler
) -> ft.Container:
    return _section_card(
        icon=ft.Icons.SOURCE,
        title="Fuente del pronostico",
        body="Selecciona la fuente que alimentara el contexto. La validacion se ejecutara al generar el pronostico.",
        extra=[
            ft.Row(
                alignment=ft.MainAxisAlignment.END,
                controls=[
                    ft.OutlinedButton(
                        "Importar CSV nuevo",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=on_import,
                    )
                ],
            ),
            source_content,
        ],
    )


def _forecast_action_panel(
    on_generate: ft.ControlEventHandler,
    loading: ft.ProgressRing,
    disabled: bool,
) -> ft.Container:
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
                ft.Text(
                    "Genera el pronostico usando la fuente y el contexto temporal seleccionados.",
                    size=13,
                    color=SECONDARY_TEXT,
                ),
                ft.Row(
                    spacing=10,
                    controls=[
                        loading,
                        ft.FilledButton(
                            "Generar pronostico",
                            disabled=disabled,
                            on_click=on_generate,
                        ),
                    ],
                ),
            ],
        ),
    )


def _last_result_content(result: dict[str, object] | None) -> ft.Container:
    if result is None:
        return _last_result_card()
    return _section_card(
        icon=ft.Icons.INSIGHTS,
        title="Ultimo resultado",
        body="Pronostico generado correctamente.",
        extra=[
            ft.ResponsiveRow(
                spacing=12,
                run_spacing=12,
                controls=[
                    _result_item("Run", str(result["run_id"])),
                    _result_item("Fuente", str(result["dataset"])),
                    _result_item("Input hasta", str(result["last_input"])),
                    _result_item("Forecast desde", str(result["first_forecast"])),
                ],
            )
        ],
    )


def _result_item(label: str, value: str) -> ft.Container:
    return ft.Container(
        col={"xs": 12, "sm": 6, "md": 3},
        padding=12,
        border=_border("#CBD5E1"),
        border_radius=10,
        bgcolor="#F8FAFC",
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Text(label, size=12, color=SECONDARY_TEXT),
                ft.Text(value, size=13, color=PRIMARY_TEXT, weight=ft.FontWeight.W_600),
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
        content=ft.Text(
            "Ejecuciones: no hay pronosticos guardados para este modelo.",
            size=13,
            color=SECONDARY_TEXT,
        ),
    )
