from __future__ import annotations

from typing import Any, Callable

import flet as ft


SECONDARY_TEXT = "#64748B"


def incremental_selector_content(
    tabs: ft.Control,
    count: ft.Control,
    item_list: ft.Control,
    load_more_button: ft.Control,
) -> ft.Column:
    return ft.Column(
        spacing=12,
        controls=[
            tabs,
            count,
            item_list,
            ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[load_more_button]),
        ],
    )


def incremental_selector_tabs(
    groups: list[str],
    active_group: str,
    label_for_group: Callable[[str], str],
    on_change: Any,
) -> ft.Control:
    if len(groups) <= 1:
        return ft.Text(label_for_group(groups[0]), size=13, color=SECONDARY_TEXT)

    return ft.Row(
        spacing=8,
        controls=[
            _selector_tab(
                label_for_group(group),
                selected=group == active_group,
                on_click=lambda _, selected_group=group: on_change(selected_group),
            )
            for group in groups
        ],
    )


def incremental_selector_group(
    title: str,
    items: list[Any],
    empty_text: str,
    item_builder: Callable[[Any], ft.Control],
) -> ft.Column:
    controls: list[ft.Control] = [
        ft.Text(title, size=13, weight=ft.FontWeight.W_600, color=SECONDARY_TEXT)
    ]
    if not items:
        controls.append(ft.Text(empty_text, size=13, color=SECONDARY_TEXT))
    else:
        controls.extend(item_builder(item) for item in items)
    return ft.Column(spacing=8, controls=controls)


def _selector_tab(
    label: str, *, selected: bool, on_click: ft.ControlEventHandler
) -> ft.Control:
    if selected:
        return ft.FilledButton(label, on_click=on_click)
    return ft.OutlinedButton(label, on_click=on_click)
