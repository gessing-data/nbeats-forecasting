from __future__ import annotations

from typing import Any

import flet as ft

from energy_forecast.desktop.components.incremental_selector import (
    incremental_selector_content,
    incremental_selector_group,
    incremental_selector_tabs,
)
from energy_forecast.desktop.features.forecast_workspace.constants import (
    BORDER_COLOR,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
)
from energy_forecast.desktop.features.forecast_workspace.sources import (
    SourceInfo,
    _available_groups,
    _source_group_title,
)
from energy_forecast.desktop.features.forecast_workspace.utils import _border


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


def _source_group(
    title: str, sources: list[SourceInfo], selected: SourceInfo | None, on_select: Any
) -> ft.Column:
    return incremental_selector_group(
        title,
        sources,
        "No hay fuentes disponibles.",
        lambda item: _source_card(item, selected, on_select),
    )


def _selected_source_summary(
    source: SourceInfo,
    on_change: ft.ControlEventHandler,
) -> ft.Container:
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
                        ft.Text(
                            "Fuente seleccionada",
                            size=13,
                            weight=ft.FontWeight.W_600,
                            color=SECONDARY_TEXT,
                        ),
                        ft.Text(
                            source.name,
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=PRIMARY_TEXT,
                        ),
                        ft.Text(
                            source.path.name,
                            size=12,
                            color=SECONDARY_TEXT,
                        ),
                    ],
                ),
                ft.OutlinedButton(
                    "Cambiar fuente", icon=ft.Icons.SWAP_HORIZ, on_click=on_change
                ),
            ],
        ),
    )


def _source_card(
    source: SourceInfo, selected: SourceInfo | None, on_select: Any
) -> ft.Container:
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
                ft.Text(
                    source.path.name,
                    size=12,
                    color=SECONDARY_TEXT,
                ),
            ],
        ),
    )
