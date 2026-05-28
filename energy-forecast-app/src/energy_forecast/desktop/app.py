import asyncio
from pathlib import Path

import flet as ft
import pandas as pd

from energy_forecast.desktop.components.app_navigation import build_app_bar
from energy_forecast.desktop.model_catalog import find_pretrained_model
from energy_forecast.desktop.navigation import navigate_to
from energy_forecast.desktop.pages.forecast_history_page import build_forecast_history_page
from energy_forecast.desktop.pages.forecast_workspace_page import build_forecast_workspace_page
from energy_forecast.desktop.pages.model_selection_page import (
    build_create_model_button,
    build_model_selection_page,
)
from energy_forecast.desktop.pages.model_creation_page import build_model_creation_page
from energy_forecast.desktop.pages.settings_page import build_settings_page


BACKGROUND_COLOR = "#F8FAFC"
APP_ROOT = Path(__file__).resolve().parents[3]


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
    pending_snackbar: dict[str, str] = {"message": ""}
    training_state: dict[str, bool | str] = {"running": False, "success": "", "error": ""}
    training_indicator = ft.Container(
        right=18,
        bottom=96,
        width=52,
        height=52,
        alignment=ft.Alignment(0, 0),
        bgcolor=ft.Colors.WHITE,
        border=ft.Border(
            ft.BorderSide(1, "#E2E8F0"),
            ft.BorderSide(1, "#E2E8F0"),
            ft.BorderSide(1, "#E2E8F0"),
            ft.BorderSide(1, "#E2E8F0"),
        ),
        border_radius=16,
        shadow=ft.BoxShadow(
            blur_radius=18,
            spread_radius=1,
            color="#33415526",
            offset=ft.Offset(0, 6),
        ),
        content=ft.ProgressRing(width=28, height=28, stroke_width=3, color="#0F172A"),
        visible=False,
    )
    page.overlay.append(training_indicator)

    def sync_training_indicator() -> None:
        training_indicator.visible = bool(training_state["running"])

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
            floating_action_button=build_create_model_button(page, disabled=bool(training_state["running"])),
        )

    def build_model_creation_view() -> ft.View:
        return build_view(
            "/models/new",
            build_model_creation_page(
                page,
                on_create=start_training,
            ),
        )

    def start_training(request: dict[str, object]) -> None:
        if training_state["running"]:
            pending_snackbar["message"] = "Ya hay un entrenamiento en curso."
            navigate_to(page, "/")
            return

        training_state["running"] = True
        training_state["success"] = ""
        training_state["error"] = ""
        sync_training_indicator()
        navigate_to(page, "/")

        def run_training_sync() -> None:
            from energy_forecast.services.training import train_nbeats_model

            source_file = request["source_file"]
            series = pd.read_csv(source_file)
            train_nbeats_model(
                    app_root=APP_ROOT,
                    title=str(request["title"]),
                    dataset_name=str(request["dataset_name"]),
                source_file=source_file,
                series=series,
                horizon=int(request["horizon"]),
                input_size=int(request["input_size"]),
                max_steps=int(request["max_steps"]),
                freq=str(request["freq"]),
                selection_mode=request["selection_mode"],
                selection_metadata=request["selection_metadata"],
                description=str(request.get("description") or ""),
            )

        async def run_training_task() -> None:
            try:
                await asyncio.to_thread(run_training_sync)
                training_state["success"] = "Modelo N-BEATS creado correctamente."
            except Exception as exc:  # noqa: BLE001 - background failures must surface in UI.
                training_state["error"] = f"No se pudo crear el modelo: {exc}"
            finally:
                training_state["running"] = False
                sync_training_indicator()
                pending_snackbar["message"] = str(training_state["error"] or training_state["success"])
                show_model_selection()

        page.run_task(run_training_task)

    def show_model_selection() -> None:
        if page.route == "/":
            route_change()
            return
        navigate_to(page, "/")

    def build_history_view() -> ft.View:
        return build_view("/history", build_forecast_history_page(), show_title=True)

    def build_settings_view() -> ft.View:
        return build_view("/settings", build_settings_page(), show_title=True)

    def build_model_workspace_view(route: str, model: dict[str, object]) -> ft.View:
        return build_view(route, build_forecast_workspace_page(model))

    def handle_model_selection_route() -> bool:
        if page.route != "/":
            return False
        page.views.append(build_model_selection_view())
        sync_training_indicator()
        success_message = pending_snackbar["message"]
        if success_message:
            pending_snackbar["message"] = ""
            page.snack_bar = ft.SnackBar(ft.Text(success_message))
            page.snack_bar.open = True
        return True

    def handle_model_creation_route() -> bool:
        if page.route != "/models/new":
            return False
        page.views.append(build_model_selection_view())
        page.views.append(build_model_creation_view())
        return True

    def handle_model_workspace_route(route: ft.TemplateRoute) -> bool:
        if not route.match("/models/:model_id"):
            return False
        model_id = str(route.model_id)
        model = find_pretrained_model(model_id)
        if model is None:
            return False
        page.views.append(build_model_selection_view())
        page.views.append(build_model_workspace_view(page.route, model))
        return True

    def handle_history_route() -> bool:
        if page.route != "/history":
            return False
        page.views.append(build_history_view())
        return True

    def handle_settings_route() -> bool:
        if page.route != "/settings":
            return False
        page.views.append(build_settings_view())
        return True

    def route_change(_: ft.RouteChangeEvent | None = None) -> None:
        route = ft.TemplateRoute(page.route)
        page.views.clear()

        handled = any(
            handler()
            for handler in (
                handle_model_selection_route,
                handle_model_creation_route,
                lambda: handle_model_workspace_route(route),
                handle_history_route,
                handle_settings_route,
            )
        )
        if not handled:
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
