from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from energy_forecast.app_paths import AppPaths
from energy_forecast.seeders.opsd_catalog import write_zone_catalog
from energy_forecast.seeders.opsd_constants import (
    OPSD_DATAPACKAGE_FILENAME,
    OPSD_RAW_FILENAME,
    OPSD_VERSION,
    ZONES_FILENAME,
)
from energy_forecast.seeders.opsd_downloader import download_datapackage, download_raw
from energy_forecast.seeders.opsd_timeseries import process_opsd_timeseries
from energy_forecast.seeders.opsd_validation import (
    SeederError,
    validate_catalog,
    validate_processed_dataset,
    validate_raw_header,
)
from energy_forecast.seeders.workspace_reset import reinstall_workspace as reset_workspace

ProgressCallback = Callable[[str, str], None]


@dataclass(frozen=True)
class SeedStatus:
    valid: bool
    raw_valid: bool
    reference_valid: bool
    processed_count: int


class OpsdSeeder:
    def __init__(self, paths: AppPaths, progress: ProgressCallback | None = None) -> None:
        self.paths = paths
        self.progress = progress or (lambda _phase, _message: None)

    @property
    def raw_path(self) -> Path:
        return self.paths.raw_data_dir / OPSD_RAW_FILENAME

    @property
    def datapackage_path(self) -> Path:
        return self.paths.raw_data_dir / OPSD_DATAPACKAGE_FILENAME

    @property
    def catalog_path(self) -> Path:
        return self.paths.reference_data_dir / ZONES_FILENAME

    def install(self) -> list[str]:
        if self.status().valid:
            raise SeederError("Los datasets OPSD ya estan instalados. Usa reparacion si necesitas regenerarlos.")
        return self._seed(force_download=False)

    def repair(self) -> list[str]:
        return self._seed(force_download=False)

    def reinstall_workspace(self) -> list[str]:
        self._emit("preparing_workspace", "Reinstalando workspace.")
        reset_workspace(self.paths)
        return self._seed(force_download=True)

    def status(self) -> SeedStatus:
        raw_valid = self._raw_valid()
        reference_valid = self._catalog_valid()
        processed_count = self._processed_count()
        return SeedStatus(
            valid=raw_valid and reference_valid and processed_count > 0,
            raw_valid=raw_valid,
            reference_valid=reference_valid,
            processed_count=processed_count,
        )

    def _seed(self, *, force_download: bool) -> list[str]:
        self._emit("preparing_workspace", "Preparando carpetas de workspace.")
        for directory in (
            self.paths.raw_data_dir,
            self.paths.processed_data_dir,
            self.paths.reference_data_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        self._ensure_raw(force_download=force_download)
        self._ensure_datapackage(force_download=force_download)

        self._emit("generating_catalog", "Generando catalogo de zonas OPSD.")
        try:
            write_zone_catalog(self.datapackage_path, self.paths.reference_data_dir)
        except SeederError:
            if force_download:
                raise
            self._emit("downloading_datapackage", "Reemplazando metadata OPSD invalida.")
            download_datapackage(self.paths.raw_data_dir)
            write_zone_catalog(self.datapackage_path, self.paths.reference_data_dir)

        self._emit("processing_timeseries", "Generando datasets procesados.")
        try:
            generated = process_opsd_timeseries(self.raw_path, self.paths.processed_data_dir)
        except SeederError:
            if force_download:
                raise
            self._emit("downloading_raw", "Reemplazando CSV crudo OPSD invalido.")
            download_raw(self.paths.raw_data_dir)
            validate_raw_header(self.raw_path)
            generated = process_opsd_timeseries(self.raw_path, self.paths.processed_data_dir)

        self._emit("validating_outputs", "Validando salidas generadas.")
        validate_catalog(self.catalog_path)
        for code in generated:
            validate_processed_dataset(self.paths.processed_data_dir / f"{code}.csv")
        self._emit("completed", "Datasets OPSD preparados correctamente.")
        return generated

    def _ensure_raw(self, *, force_download: bool) -> None:
        self._emit("validating_raw", "Validando CSV crudo OPSD.")
        if not force_download:
            try:
                validate_raw_header(self.raw_path)
                return
            except SeederError:
                pass
        self._emit("downloading_raw", "Descargando CSV crudo OPSD.")
        download_raw(self.paths.raw_data_dir)
        validate_raw_header(self.raw_path)

    def _ensure_datapackage(self, *, force_download: bool) -> None:
        if self.datapackage_path.exists() and not force_download:
            return
        self._emit("downloading_datapackage", "Descargando metadata OPSD.")
        download_datapackage(self.paths.raw_data_dir)

    def _raw_valid(self) -> bool:
        try:
            validate_raw_header(self.raw_path)
        except SeederError:
            return False
        return True

    def _catalog_valid(self) -> bool:
        try:
            validate_catalog(self.catalog_path)
        except SeederError:
            return False
        return True

    def _processed_count(self) -> int:
        if not self.paths.processed_data_dir.exists():
            return 0
        count = 0
        for path in self.paths.processed_data_dir.glob("*.csv"):
            try:
                validate_processed_dataset(path)
            except SeederError:
                continue
            count += 1
        return count

    def _emit(self, phase: str, message: str) -> None:
        self.progress(phase, message)


def successful_seed_settings(existing: dict[str, object]) -> dict[str, object]:
    updated = dict(existing)
    seeds = dict(updated.get("seeds", {}))
    now = datetime.now(UTC).isoformat()
    seeds.setdefault("initialized_at", now)
    if not seeds.get("initialized_at"):
        seeds["initialized_at"] = now
    seeds.update(
        {
            "initialized": True,
            "updated_at": now,
            "source": "opsd",
            "source_version": OPSD_VERSION,
            "raw_downloaded": True,
            "processed_generated": True,
            "reference_generated": True,
            "last_error": None,
        }
    )
    updated["seeds"] = seeds
    return updated


def failed_seed_settings(existing: dict[str, object], error: Exception) -> dict[str, object]:
    updated = dict(existing)
    seeds = dict(updated.get("seeds", {}))
    seeds["initialized"] = False
    seeds["last_error"] = str(error)
    updated["seeds"] = seeds
    return updated
