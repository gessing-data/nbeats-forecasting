from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from energy_forecast.app_paths import AppPaths, load_settings, save_settings
from energy_forecast.seeders.opsd_seeder import (
    OpsdSeeder,
    failed_seed_settings,
    successful_seed_settings,
)

ProgressCallback = Callable[[str, str], None]


@dataclass(frozen=True)
class DatasetSeedingResult:
    ok: bool
    message: str
    generated_count: int = 0


def install_datasets(
    paths: AppPaths, progress: ProgressCallback | None = None
) -> DatasetSeedingResult:
    return _run_action(paths, "install", progress)


def repair_datasets(
    paths: AppPaths, progress: ProgressCallback | None = None
) -> DatasetSeedingResult:
    return _run_action(paths, "repair", progress)


def reinstall_workspace(
    paths: AppPaths, progress: ProgressCallback | None = None
) -> DatasetSeedingResult:
    return _run_action(paths, "reinstall", progress)


def _run_action(
    paths: AppPaths,
    action: str,
    progress: ProgressCallback | None,
) -> DatasetSeedingResult:
    seeder = OpsdSeeder(paths, progress=progress)
    try:
        if action == "install":
            generated = seeder.install()
        elif action == "repair":
            generated = seeder.repair()
        elif action == "reinstall":
            generated = seeder.reinstall_workspace()
        else:
            raise ValueError(f"accion no soportada: {action}")
    except Exception as exc:  # noqa: BLE001 - service boundary translates errors for UI.
        save_settings(paths, failed_seed_settings(load_settings(paths), exc))
        if progress is not None:
            progress("failed", str(exc))
        return DatasetSeedingResult(ok=False, message=str(exc))

    if progress is not None:
        progress("updating_settings", "Actualizando configuracion.")
    save_settings(paths, successful_seed_settings(load_settings(paths)))
    message = f"Datasets OPSD listos: {len(generated)} zonas procesadas."
    return DatasetSeedingResult(ok=True, message=message, generated_count=len(generated))
