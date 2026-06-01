from __future__ import annotations

import flet as ft


def show_destructive_confirmation(
    page: ft.Page,
    *,
    title: str,
    message: str,
    confirm_label: str = "Borrar",
    on_confirm: ft.ControlEventHandler,
) -> None:
    def close_dialog(_: ft.ControlEvent | None = None) -> None:
        page.pop_dialog()

    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dialog),
                ft.TextButton(
                    confirm_label,
                    style=ft.ButtonStyle(color="#DC2626"),
                    on_click=on_confirm,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    )
