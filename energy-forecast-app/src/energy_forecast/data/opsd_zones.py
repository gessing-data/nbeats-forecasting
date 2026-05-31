import pandas as pd

from energy_forecast.app_paths import AppPaths, resolve_app_paths

REQUIRED_COLUMNS = {"code", "name"}


def load_opsd_zones(paths: AppPaths | None = None) -> pd.DataFrame:
    app_paths = paths or resolve_app_paths()
    zones_path = app_paths.reference_data_dir / "opsd_zones.csv"
    try:
        zones = pd.read_csv(zones_path, dtype=str).fillna("")
    except (OSError, pd.errors.ParserError):
        return pd.DataFrame(columns=sorted(REQUIRED_COLUMNS))

    if not REQUIRED_COLUMNS.issubset(zones.columns):
        return pd.DataFrame(columns=sorted(REQUIRED_COLUMNS))

    return zones


def load_opsd_zone_names(paths: AppPaths | None = None) -> dict[str, str]:
    zones = load_opsd_zones(paths)
    if zones.empty:
        return {}

    return dict(zip(zones["code"], zones["name"], strict=False))
