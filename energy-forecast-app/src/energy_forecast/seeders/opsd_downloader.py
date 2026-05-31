from __future__ import annotations

from pathlib import Path
from urllib.error import URLError
from urllib.request import urlretrieve

from energy_forecast.seeders.opsd_constants import (
    OPSD_DATAPACKAGE_FILENAME,
    OPSD_DATAPACKAGE_URL,
    OPSD_RAW_FILENAME,
    OPSD_RAW_URL,
)
from energy_forecast.seeders.opsd_validation import SeederError


def download_file(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(destination.suffix + ".tmp")
    try:
        urlretrieve(url, temp_path)  # noqa: S310 - URLs are fixed OPSD constants.
        temp_path.replace(destination)
    except (OSError, URLError) as exc:
        temp_path.unlink(missing_ok=True)
        raise SeederError(f"No se pudo descargar {destination.name}.") from exc
    return destination


def download_raw(raw_dir: Path) -> Path:
    return download_file(OPSD_RAW_URL, raw_dir / OPSD_RAW_FILENAME)


def download_datapackage(raw_dir: Path) -> Path:
    return download_file(OPSD_DATAPACKAGE_URL, raw_dir / OPSD_DATAPACKAGE_FILENAME)
