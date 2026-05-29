from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from energy_forecast.seeders.opsd_constants import (
    OPSD_RAW_FILENAME,
    TARGET_VARIABLE,
    ZONES_FILENAME,
)
from energy_forecast.seeders.opsd_validation import SeederError


def load_datapackage(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SeederError("No se pudo leer datapackage.json.") from exc
    if not isinstance(data, dict):
        raise SeederError("datapackage.json no tiene formato valido.")
    return data


def find_resource(datapackage: dict[str, Any]) -> dict[str, Any]:
    for resource in datapackage.get("resources", []):
        if isinstance(resource, dict) and resource.get("path") == OPSD_RAW_FILENAME:
            return resource
    raise SeederError(f"No se encontro el recurso {OPSD_RAW_FILENAME}.")


def zone_name_from_description(description: str) -> str:
    name = re.sub(r"^Total load in ", "", description)
    name = re.sub(r" in MW.*$", "", name)
    return re.sub(r"\s*\((control area|bidding zone)\)\s*", "", name).strip()


def zone_kind_from_description(description: str) -> str:
    if "(control area)" in description:
        return "control_area"
    if "(bidding zone)" in description:
        return "bidding_zone"
    if description.startswith("Total load in "):
        return "country"
    return "unknown"


def build_zone_catalog(datapackage: dict[str, Any]) -> pd.DataFrame:
    resource = find_resource(datapackage)
    rows: list[dict[str, str]] = []
    for field in resource.get("schema", {}).get("fields", []):
        if not isinstance(field, dict):
            continue
        properties = field.get("opsdProperties", {})
        if not isinstance(properties, dict) or properties.get("Variable") != TARGET_VARIABLE:
            continue
        description = str(field.get("description", ""))
        rows.append(
            {
                "code": str(properties.get("Region", "")),
                "name": zone_name_from_description(description),
                "kind": zone_kind_from_description(description),
                "source_variable": str(properties.get("Variable", "")),
                "source_description": description,
            }
        )
    zones = pd.DataFrame(rows)
    if zones.empty:
        raise SeederError("No se encontraron zonas OPSD para la variable objetivo.")
    zones = zones.drop_duplicates(subset=["code"]).sort_values("code").reset_index(drop=True)
    if zones["code"].eq("").any():
        raise SeederError("El catalogo OPSD contiene zonas sin codigo.")
    return zones


def write_zone_catalog(datapackage_path: Path, reference_dir: Path) -> Path:
    reference_dir.mkdir(parents=True, exist_ok=True)
    output_path = reference_dir / ZONES_FILENAME
    catalog = build_zone_catalog(load_datapackage(datapackage_path))
    catalog.to_csv(output_path, index=False)
    return output_path
