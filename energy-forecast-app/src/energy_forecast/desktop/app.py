from pathlib import Path
import os
import sys
from typing import TextIO

import flet as ft

from energy_forecast.app_paths import prepare_workspace
from energy_forecast.desktop.background_operations import BackgroundOperations
from energy_forecast.desktop.layout import BACKGROUND_COLOR
from energy_forecast.desktop.router import DesktopRouter
from energy_forecast.desktop.seeding_controller import SeedingController
from energy_forecast.desktop.training_controller import TrainingController


_STDIO_HANDLES: list[TextIO] = []


def main(page: ft.Page) -> None:
    paths = prepare_workspace()
    _ensure_standard_streams(paths.workspace_root / "logs" / "app.log")

    page.title = "Energy Forecast App"
    page.bgcolor = BACKGROUND_COLOR
    page.padding = 0

    if page.window:
        page.window.width = 1100
        page.window.height = 760
        page.window.min_width = 420
        page.window.min_height = 560

    background = BackgroundOperations(page)
    training = TrainingController(page, paths, background)
    seeding = SeedingController(page, paths, background)
    DesktopRouter(page, paths, training, seeding, background).attach()


def run_app() -> None:
    ft.run(main)


def _ensure_standard_streams(log_path: Path) -> None:
    """Provide stdout/stderr for GUI bundles that start without a console."""
    if sys.stdout is not None and sys.stderr is not None:
        return

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        stream = log_path.open("a", encoding="utf-8", buffering=1)
    except OSError:
        stream = open(os.devnull, "w", encoding="utf-8")

    _STDIO_HANDLES.append(stream)
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream


if __name__ == "__main__":
    run_app()
