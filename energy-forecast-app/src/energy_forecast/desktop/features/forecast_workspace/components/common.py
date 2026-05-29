from __future__ import annotations

import flet as ft

from energy_forecast.desktop.features.forecast_workspace.constants import (
    BORDER_COLOR,
    PRIMARY_TEXT,
    SECONDARY_TEXT,
)
from energy_forecast.desktop.features.forecast_workspace.utils import _border


def _section_card(
    *,
    icon: str,
    title: str,
    body: str,
    footer: str | None = None,
    extra: list[ft.Control] | None = None,
) -> ft.Container:
    controls: list[ft.Control] = [
        ft.Row(
            spacing=10,
            controls=[
                ft.Icon(icon, size=20, color=SECONDARY_TEXT),
                ft.Text(title, size=17, weight=ft.FontWeight.W_600, color=PRIMARY_TEXT),
            ],
        ),
        ft.Text(body, size=13, color=SECONDARY_TEXT),
    ]
    if footer:
        controls.append(
            ft.Text(footer, size=12, color="#475569", weight=ft.FontWeight.W_500)
        )
    controls.extend(extra or [])
    return ft.Container(
        width=float("inf"),
        padding=16,
        border=_border(BORDER_COLOR),
        border_radius=14,
        bgcolor=ft.Colors.WHITE,
        content=ft.Column(spacing=10, controls=controls),
    )


def _card(content: ft.Control) -> ft.Container:
    return ft.Container(
        width=float("inf"),
        padding=18,
        bgcolor=ft.Colors.WHITE,
        border=_border(BORDER_COLOR),
        border_radius=16,
        content=content,
    )
