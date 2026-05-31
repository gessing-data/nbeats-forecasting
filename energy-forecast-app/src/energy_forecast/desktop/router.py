import flet as ft

from energy_forecast.app_paths import AppPaths
from energy_forecast.desktop.components.app_navigation import build_app_bar
from energy_forecast.desktop.features.forecast_history.page import build_forecast_history_page
from energy_forecast.desktop.features.forecast_workspace.page import build_forecast_workspace_page
from energy_forecast.desktop.features.model_creation.page import build_model_creation_page
from energy_forecast.desktop.features.model_selection.page import (
    build_create_model_button,
    build_model_selection_page,
)
from energy_forecast.desktop.features.settings.page import build_settings_page
from energy_forecast.desktop.layout import BACKGROUND_COLOR
from energy_forecast.desktop.navigation import navigate_to
from energy_forecast.desktop.seeding_controller import SeedingController
from energy_forecast.desktop.training_controller import TrainingController
from energy_forecast.storage.model_catalog import find_pretrained_model


class DesktopRouter:
    def __init__(
        self,
        page: ft.Page,
        paths: AppPaths,
        training: TrainingController,
        seeding: SeedingController,
    ) -> None:
        self.page = page
        self.paths = paths
        self.training = training
        self.seeding = seeding
        self.selection_state: dict[str, str] = {
            "query": "",
            "zone": "",
            "horizon": "",
            "input_size": "",
            "frequency": "",
            "max_steps": "",
        }

    def attach(self) -> None:
        self.page.on_route_change = self.route_change
        self.page.on_view_pop = self.view_pop
        self.page.route = self.page.route or "/"
        self.route_change()

    def route_change(self, _: ft.RouteChangeEvent | None = None) -> None:
        route = ft.TemplateRoute(self.page.route)
        self.page.views.clear()

        handled = any(
            handler()
            for handler in (
                self._handle_model_selection_route,
                self._handle_model_creation_route,
                lambda: self._handle_model_workspace_route(route),
                self._handle_history_route,
                self._handle_settings_route,
            )
        )
        if not handled:
            navigate_to(self.page, "/")
            return

        self.page.update()

    def view_pop(self, _: ft.ViewPopEvent) -> None:
        if len(self.page.views) > 1:
            self.page.views.pop()
            navigate_to(self.page, self.page.views[-1].route)
        else:
            navigate_to(self.page, "/")

    def _build_view(
        self,
        route: str,
        content: ft.Control,
        show_title: bool = False,
        floating_action_button: ft.FloatingActionButton | None = None,
    ) -> ft.View:
        return ft.View(
            route=route,
            appbar=build_app_bar(self.page, show_title=show_title),
            controls=[content],
            bgcolor=BACKGROUND_COLOR,
            padding=0,
            scroll=ft.ScrollMode.AUTO,
            floating_action_button=floating_action_button,
        )

    def _model_selection_view(self) -> ft.View:
        return self._build_view(
            "/",
            build_model_selection_page(self.page, self.selection_state, self.paths),
            show_title=True,
            floating_action_button=build_create_model_button(
                self.page,
                disabled=self.training.running,
            ),
        )

    def _model_creation_view(self) -> ft.View:
        return self._build_view(
            "/models/new",
            build_model_creation_page(
                self.page,
                self.paths,
                on_create=self.training.start_training,
            ),
        )

    def _handle_model_selection_route(self) -> bool:
        if self.page.route != "/":
            return False
        self.page.views.append(self._model_selection_view())
        self.training.sync_background_operation()
        message = self.training.pop_pending_message()
        if message:
            self.page.snack_bar = ft.SnackBar(ft.Text(message))
            self.page.snack_bar.open = True
        return True

    def _handle_model_creation_route(self) -> bool:
        if self.page.route != "/models/new":
            return False
        self.page.views.append(self._model_selection_view())
        self.page.views.append(self._model_creation_view())
        return True

    def _handle_model_workspace_route(self, route: ft.TemplateRoute) -> bool:
        if not route.match("/models/:model_id"):
            return False
        model = find_pretrained_model(str(route.model_id), self.paths)
        if model is None:
            return False
        self.page.views.append(self._model_selection_view())
        self.page.views.append(
            self._build_view(
                self.page.route,
                build_forecast_workspace_page(self.page, self.paths, model),
            )
        )
        return True

    def _handle_history_route(self) -> bool:
        if self.page.route != "/history":
            return False
        self.page.views.append(
            self._build_view(
                "/history",
                build_forecast_history_page(self.page, self.paths),
                show_title=True,
            )
        )
        return True

    def _handle_settings_route(self) -> bool:
        if self.page.route != "/settings":
            return False
        self.page.views.append(
            self._build_view(
                "/settings",
                build_settings_page(self.page, self.paths, self.seeding),
                show_title=True,
            )
        )
        return True
