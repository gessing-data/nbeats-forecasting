"""Application workspace paths and settings."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


WORKSPACE_DIR_NAME = "Energy Forecast app"
WORKSPACE_VERSION = 1


@dataclass(frozen=True)
class AppPaths:
    """Resolved paths for the external user workspace."""

    workspace_root: Path
    settings_path: Path
    data_dir: Path
    raw_data_dir: Path
    processed_data_dir: Path
    imported_data_dir: Path
    reference_data_dir: Path
    models_dir: Path


def default_workspace_root() -> Path:
    """Return the default user-visible workspace location."""
    return Path.home() / WORKSPACE_DIR_NAME


def resolve_app_paths(workspace_root: str | Path | None = None) -> AppPaths:
    """Build all application paths from the workspace root."""
    root = Path(workspace_root) if workspace_root is not None else default_workspace_root()
    data_dir = root / "data"

    return AppPaths(
        workspace_root=root,
        settings_path=root / "settings.json",
        data_dir=data_dir,
        raw_data_dir=data_dir / "raw",
        processed_data_dir=data_dir / "processed",
        imported_data_dir=data_dir / "imported",
        reference_data_dir=data_dir / "reference",
        models_dir=root / "models",
    )


def ensure_workspace_directories(paths: AppPaths) -> None:
    """Create the workspace directory tree if needed."""
    for directory in (
        paths.raw_data_dir,
        paths.processed_data_dir,
        paths.imported_data_dir,
        paths.reference_data_dir,
        paths.models_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def default_settings() -> dict[str, Any]:
    """Return a new default settings payload."""
    return {
        "workspace_version": WORKSPACE_VERSION,
        "seeds": {
            "initialized": False,
            "initialized_at": None,
            "source": "opsd",
            "raw_downloaded": False,
            "processed_generated": False,
            "reference_generated": False,
        },
    }


def load_settings(paths: AppPaths) -> dict[str, Any]:
    """Load workspace settings, returning defaults when missing or invalid."""
    try:
        data = json.loads(paths.settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_settings()

    if not isinstance(data, dict):
        return default_settings()

    return _merge_settings(default_settings(), data)


def save_settings(paths: AppPaths, settings: dict[str, Any]) -> None:
    """Persist workspace settings."""
    paths.workspace_root.mkdir(parents=True, exist_ok=True)
    paths.settings_path.write_text(
        json.dumps(settings, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def prepare_workspace(workspace_root: str | Path | None = None) -> AppPaths:
    """Create required workspace files and return resolved paths."""
    paths = resolve_app_paths(workspace_root)
    ensure_workspace_directories(paths)
    if not paths.settings_path.exists():
        save_settings(paths, default_settings())
    else:
        save_settings(paths, load_settings(paths))
    return paths


def _merge_settings(default: dict[str, Any], loaded: dict[str, Any]) -> dict[str, Any]:
    merged = dict(default)
    for key, value in loaded.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_settings(merged[key], value)
        else:
            merged[key] = value
    return merged
