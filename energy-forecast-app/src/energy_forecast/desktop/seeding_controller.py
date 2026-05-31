from __future__ import annotations

import asyncio

import flet as ft

from energy_forecast.app_paths import AppPaths
from energy_forecast.desktop.background_operations import BackgroundOperations
from energy_forecast.services.dataset_seeding import (
    DatasetSeedingResult,
    install_datasets,
    repair_datasets,
    reinstall_workspace,
)


class SeedingController:
    def __init__(self, page: ft.Page, paths: AppPaths, background: BackgroundOperations) -> None:
        self.page = page
        self.paths = paths
        self.background = background
        self.running = False
        self.message = "Sin operacion en curso."

    def start(self, action: str) -> None:
        if self.running:
            self._snackbar("Ya hay una operacion de datasets en curso.")
            return
        self.running = True
        self.message = "Iniciando operacion de datasets."
        self.background.show("Datasets OPSD", self.message, key="seeding")
        self._refresh_current_page()

        async def task() -> None:
            result = await asyncio.to_thread(self._run_sync, action)
            self.running = False
            self.message = result.message
            self.background.finish(
                "Datasets OPSD",
                result.message,
                success=result.ok,
                key="seeding",
            )
            self._snackbar(result.message)
            self._refresh_current_page()

        self.page.run_task(task)

    def progress_text(self) -> str:
        return self.message

    def _run_sync(self, action: str) -> DatasetSeedingResult:
        service = {
            "install": install_datasets,
            "repair": repair_datasets,
            "reinstall": reinstall_workspace,
        }[action]
        return service(self.paths, self._update_progress)

    def _update_progress(self, phase: str, message: str) -> None:
        self.message = f"{_phase_label(phase)}: {message}"
        self.background.show("Datasets OPSD", self.message, key="seeding")
        self._refresh_current_page()

    def _snackbar(self, message: str) -> None:
        self.page.snack_bar = ft.SnackBar(ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    def _refresh_current_page(self) -> None:
        if self.page.route == "/settings" and self.page.on_route_change is not None:
            self.page.on_route_change(None)


def _phase_label(phase: str) -> str:
    return {
        "preparing_workspace": "Preparando workspace",
        "validating_raw": "Validando raw",
        "downloading_raw": "Descargando raw",
        "downloading_datapackage": "Descargando metadata",
        "generating_catalog": "Generando catalogo",
        "processing_timeseries": "Procesando series",
        "validating_outputs": "Validando salidas",
        "updating_settings": "Actualizando settings",
        "completed": "Completado",
        "failed": "Error",
    }.get(phase, phase)
