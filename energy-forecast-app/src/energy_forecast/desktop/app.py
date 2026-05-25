import flet as ft

from energy_forecast.desktop.components.app_navigation import build_app_bar
from energy_forecast.desktop.model_catalog import find_pretrained_model
from energy_forecast.desktop.navigation import navigate_to
from energy_forecast.desktop.pages.forecast_history_page import build_forecast_history_page
from energy_forecast.desktop.pages.forecast_workspace_page import build_forecast_workspace_page
from energy_forecast.desktop.pages.model_selection_page import (
    build_create_model_button,
    build_model_selection_page,
)
from energy_forecast.desktop.pages.settings_page import build_settings_page


BACKGROUND_COLOR = "#F8FAFC"


def main(page: ft.Page) -> None:
    page.title = "Energy Forecast App"
    page.bgcolor = BACKGROUND_COLOR
    page.padding = 0

    if page.window:
        page.window.width = 1100
        page.window.height = 760
        page.window.min_width = 420
        page.window.min_height = 560

    selection_state: dict[str, str] = {
        "query": "",
        "zone": "",
        "horizon": "",
        "input_size": "",
        "frequency": "",
        "max_steps": "",
    }

    def build_view(
        route: str,
        content: ft.Control,
        show_title: bool = False,
        floating_action_button: ft.FloatingActionButton | None = None,
    ) -> ft.View:
        return ft.View(
            route=route,
            appbar=build_app_bar(page, show_title=show_title),
            controls=[content],
            bgcolor=BACKGROUND_COLOR,
            padding=0,
            scroll=ft.ScrollMode.AUTO,
            floating_action_button=floating_action_button,
        )

    def build_model_selection_view() -> ft.View:
        return build_view(
            "/",
            build_model_selection_page(page, selection_state),
            show_title=True,
            floating_action_button=build_create_model_button(),
        )

    def build_history_view() -> ft.View:
        return build_view("/history", build_forecast_history_page(), show_title=True)

    def build_settings_view() -> ft.View:
        return build_view("/settings", build_settings_page(), show_title=True)

    def build_model_workspace_view(route: str, model: dict[str, object]) -> ft.View:
        return build_view(route, build_forecast_workspace_page(model))

    def route_change(_: ft.RouteChangeEvent | None = None) -> None:
        route = ft.TemplateRoute(page.route)
        page.views.clear()

        if page.route == "/":
            page.views.append(build_model_selection_view())
        elif route.match("/models/:model_id"):
            model_id = str(route.model_id)
            model = find_pretrained_model(model_id)
            if model is None:
                navigate_to(page, "/")
                return
            page.views.append(build_model_selection_view())
            page.views.append(build_model_workspace_view(page.route, model))
        elif page.route == "/history":
            page.views.append(build_history_view())
        elif page.route == "/settings":
            page.views.append(build_settings_view())
        else:
            navigate_to(page, "/")
            return

        page.update()

    def view_pop(event: ft.ViewPopEvent) -> None:
        if len(page.views) > 1:
            page.views.pop()
            navigate_to(page, page.views[-1].route)
        else:
            navigate_to(page, "/")

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.route = page.route or "/"
    route_change()


def run_app() -> None:
    ft.run(main)


if __name__ == "__main__":
    run_app()
