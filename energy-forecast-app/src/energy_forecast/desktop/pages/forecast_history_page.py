import flet as ft


def build_forecast_history_page() -> ft.Control:
    return _placeholder_page("Historial de forecasts")


def _placeholder_page(title: str) -> ft.Container:
    return ft.Container(
        expand=True,
        bgcolor="#F8FAFC",
        alignment=ft.Alignment(0, -1),
        content=ft.Container(
            width=968,
            padding=ft.Padding(24, 28, 24, 28),
            content=ft.Column(
                spacing=8,
                controls=[
                    _page_title(title),
                ],
            ),
        ),
    )


def _page_title(title: str) -> ft.Text:
    return ft.Text(
        title,
        size=28,
        weight=ft.FontWeight.W_600,
        color="#0F172A",
    )
