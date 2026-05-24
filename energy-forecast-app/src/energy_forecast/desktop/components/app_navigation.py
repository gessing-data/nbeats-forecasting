import flet as ft

from energy_forecast.desktop.navigation import navigate_to


def build_app_bar(page: ft.Page, show_title: bool = False) -> ft.AppBar:
    return ft.AppBar(
        bgcolor=ft.Colors.WHITE,
        elevation=0,
        color="#334155",
        title=_app_title() if show_title else None,
        actions=_navigation_actions(page),
    )


def _app_title() -> ft.Text:
    return ft.Text("Energy Forecast", weight=ft.FontWeight.W_600, color="#0F172A")


def _navigation_actions(page: ft.Page) -> list[ft.IconButton]:
    return [
        _navigation_button(
            page=page,
            icon=ft.Icons.MODEL_TRAINING_OUTLINED,
            tooltip="Seleccion de modelos",
            route="/",
        ),
        _navigation_button(
            page=page,
            icon=ft.Icons.HISTORY,
            tooltip="Historial de forecasts",
            route="/history",
        ),
        _navigation_button(
            page=page,
            icon=ft.Icons.SETTINGS_OUTLINED,
            tooltip="Configuracion",
            route="/settings",
        ),
    ]


def _navigation_button(
    page: ft.Page,
    icon: str,
    tooltip: str,
    route: str,
) -> ft.IconButton:
    return ft.IconButton(
        icon=icon,
        tooltip=tooltip,
        icon_color="#334155",
        on_click=lambda _: navigate_to(page, route),
    )
