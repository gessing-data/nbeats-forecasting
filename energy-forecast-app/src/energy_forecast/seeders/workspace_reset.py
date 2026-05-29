from __future__ import annotations

import shutil

from energy_forecast.app_paths import (
    AppPaths,
    default_settings,
    ensure_workspace_directories,
    load_settings,
    save_settings,
)


def reset_seeds(settings: dict[str, object]) -> dict[str, object]:
    updated = dict(settings)
    updated["seeds"] = default_settings()["seeds"]
    return updated


def reinstall_workspace(paths: AppPaths) -> None:
    settings = reset_seeds(load_settings(paths))
    shutil.rmtree(paths.data_dir, ignore_errors=True)
    shutil.rmtree(paths.models_dir, ignore_errors=True)
    ensure_workspace_directories(paths)
    save_settings(paths, settings)
