from pathlib import Path

import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[3]
OPSD_ZONES_PATH = APP_ROOT / "data" / "reference" / "opsd_zones.csv"
REQUIRED_COLUMNS = {"code", "name"}


def load_opsd_zones() -> pd.DataFrame:
    try:
        zones = pd.read_csv(OPSD_ZONES_PATH, dtype=str).fillna("")
    except (OSError, pd.errors.ParserError):
        return pd.DataFrame(columns=sorted(REQUIRED_COLUMNS))

    if not REQUIRED_COLUMNS.issubset(zones.columns):
        return pd.DataFrame(columns=sorted(REQUIRED_COLUMNS))

    return zones


def load_opsd_zone_names() -> dict[str, str]:
    zones = load_opsd_zones()
    if zones.empty:
        return {}

    return dict(zip(zones["code"], zones["name"], strict=False))
