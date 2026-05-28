import flet as ft

from energy_forecast.desktop.layout import page_shell


def build_forecast_history_page() -> ft.Control:
    return _placeholder_page("Historial de forecasts")


def _placeholder_page(title: str) -> ft.Container:
    return page_shell(
        ft.Column(
            spacing=8,
            controls=[
                _page_title(title),
            ],
        )
    )


def _page_title(title: str) -> ft.Text:
    return ft.Text(
        title,
        size=28,
        weight=ft.FontWeight.W_600,
        color="#0F172A",
    )
