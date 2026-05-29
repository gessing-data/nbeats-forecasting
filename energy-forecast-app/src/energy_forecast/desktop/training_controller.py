import asyncio
from pathlib import Path

import flet as ft
import pandas as pd

from energy_forecast.app_paths import AppPaths
from energy_forecast.desktop.background_operations import BackgroundOperations
from energy_forecast.desktop.navigation import navigate_to


class TrainingController:
    def __init__(
        self,
        page: ft.Page,
        paths: AppPaths,
        background: BackgroundOperations | None = None,
    ) -> None:
        self.page = page
        self.paths = paths
        self.background = background
        self.state: dict[str, bool | str] = {
            "running": False,
            "success": "",
            "error": "",
        }
        self.pending_snackbar: dict[str, str] = {"message": ""}
        self.indicator = _training_indicator()
        self.page.overlay.append(self.indicator)

    @property
    def running(self) -> bool:
        return bool(self.state["running"])

    def sync_indicator(self) -> None:
        self.indicator.visible = self.running
        if self.background is not None:
            if self.running:
                self.background.show(
                    "Entrenamiento de modelo",
                    "Creando modelo N-BEATS.",
                    key="training",
                )
            else:
                self.background.hide(key="training")

    def pop_pending_message(self) -> str:
        message = self.pending_snackbar["message"]
        self.pending_snackbar["message"] = ""
        return message

    def start_training(self, request: dict[str, object]) -> None:
        if self.running:
            self.pending_snackbar["message"] = "Ya hay un entrenamiento en curso."
            self._show_model_selection()
            return

        self.state["running"] = True
        self.state["success"] = ""
        self.state["error"] = ""
        self.sync_indicator()
        navigate_to(self.page, "/")

        async def run_training_task() -> None:
            try:
                await asyncio.to_thread(self._run_training_sync, request)
                self.state["success"] = "Modelo N-BEATS creado correctamente."
            except Exception as exc:  # noqa: BLE001 - background failures must surface in UI.
                self.state["error"] = f"No se pudo crear el modelo: {exc}"
            finally:
                self.state["running"] = False
                message = str(self.state["error"] or self.state["success"])
                if self.background is not None:
                    self.background.finish(
                        "Entrenamiento de modelo",
                        message,
                        success=not bool(self.state["error"]),
                        key="training",
                    )
                self.indicator.visible = False
                self.pending_snackbar["message"] = message
                self._show_model_selection()

        self.page.run_task(run_training_task)

    def _show_model_selection(self) -> None:
        if self.page.route == "/" and self.page.on_route_change is not None:
            self.page.on_route_change(None)
            return
        navigate_to(self.page, "/")

    def _run_training_sync(self, request: dict[str, object]) -> None:
        from energy_forecast.services.training import train_nbeats_model

        source_file = Path(request["source_file"])
        series = pd.read_csv(source_file)
        train_nbeats_model(
            app_root=self.paths.workspace_root,
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


def _training_indicator() -> ft.Container:
    return ft.Container(
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
