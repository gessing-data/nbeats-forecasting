import flet as ft


BACKGROUND_COLOR = "#F8FAFC"
MAX_CONTENT_WIDTH = 920
PAGE_PADDING = 24


def page_shell(content: ft.Control) -> ft.Container:
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
