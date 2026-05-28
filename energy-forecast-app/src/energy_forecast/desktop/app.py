import flet as ft

from energy_forecast.app_paths import prepare_workspace
from energy_forecast.desktop.layout import BACKGROUND_COLOR
from energy_forecast.desktop.router import DesktopRouter
from energy_forecast.desktop.training_controller import TrainingController


def main(page: ft.Page) -> None:
    paths = prepare_workspace()

    page.title = "Energy Forecast App"
    page.bgcolor = BACKGROUND_COLOR
    page.padding = 0

    if page.window:
        page.window.width = 1100
        page.window.height = 760
        page.window.min_width = 420
        page.window.min_height = 560

    training = TrainingController(page, paths)
    DesktopRouter(page, paths, training).attach()


def run_app() -> None:
    ft.run(main)


if __name__ == "__main__":
    run_app()
