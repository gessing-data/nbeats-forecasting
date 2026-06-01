"""Compute device selection for NeuralForecast models."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import subprocess
from typing import Any


DEFAULT_COMPUTE_SELECTION = "auto"


@dataclass(frozen=True)
class ComputeDevice:
    """Device option exposed to the app settings."""

    id: str
    label: str
    accelerator: str
    devices: int | list[int] | None
    available: bool = True
    reason: str = ""


@lru_cache(maxsize=1)
def available_compute_devices() -> list[ComputeDevice]:
    """Return CPU, PyTorch-usable GPUs, and detected-but-unusable GPUs."""
    torch_info = _torch_accelerator_info()
    devices = [
        ComputeDevice(
            id="auto",
            label="Automatico (CPU)",
            accelerator="auto",
            devices=None,
        ),
        ComputeDevice(id="cpu", label="CPU", accelerator="cpu", devices=1),
    ]

    torch = torch_info.get("torch")
    cuda_available = bool(torch_info.get("cuda_available"))
    cuda_device_count = int(torch_info.get("cuda_device_count") or 0)
    cuda_visible_ids: set[int] = set()
    if torch is not None and cuda_available:
        for index in range(cuda_device_count):
            name = torch.cuda.get_device_name(index) or f"CUDA GPU {index}"
            cuda_visible_ids.add(index)
            devices.append(
                ComputeDevice(
                    id=f"cuda:{index}",
                    label=f"GPU {index}: {name}",
                    accelerator="gpu",
                    devices=[index],
                )
            )

    for index, name in _nvidia_smi_gpus():
        if index in cuda_visible_ids:
            continue
        devices.append(
            ComputeDevice(
                id=f"unavailable:cuda:{index}",
                label=f"GPU {index}: {name} (no disponible para PyTorch)",
                accelerator="gpu",
                devices=[index],
                available=False,
                reason=_cuda_unavailable_reason(torch_info),
            )
        )

    mps_available = bool(torch_info.get("mps_available"))
    if mps_available:
        devices.append(
            ComputeDevice(
                id="mps",
                label="GPU Apple Metal (MPS)",
                accelerator="mps",
                devices=1,
            )
        )

    devices[0] = ComputeDevice(
        id="auto",
        label=f"Automatico ({_auto_device(devices).label})",
        accelerator="auto",
        devices=None,
    )

    return devices


def resolve_compute_device(selection: str | None) -> ComputeDevice:
    """Resolve a persisted selection, falling back safely to auto/CPU."""
    selected = (selection or DEFAULT_COMPUTE_SELECTION).strip() or DEFAULT_COMPUTE_SELECTION
    devices = available_compute_devices()
    match = next((device for device in devices if device.id == selected), None)
    if match is not None:
        if not match.available:
            raise RuntimeError(match.reason or f"{match.label} no esta disponible")
        if match.id == "auto":
            return _auto_device(devices)
        return match

    return _auto_device(devices)


def compute_trainer_kwargs(selection: str | None) -> dict[str, Any]:
    """Build NeuralForecast/PyTorch Lightning kwargs for the selected device."""
    device = resolve_compute_device(selection)
    kwargs: dict[str, Any] = {"accelerator": device.accelerator}
    if device.devices is not None:
        kwargs["devices"] = device.devices
    return kwargs


def compute_metadata(selection: str | None) -> dict[str, Any]:
    """Return serializable metadata describing the selected compute target."""
    requested = (selection or DEFAULT_COMPUTE_SELECTION).strip() or DEFAULT_COMPUTE_SELECTION
    devices = available_compute_devices()
    selected = next((device for device in devices if device.id == requested), None)
    if selected is None:
        selected = next(device for device in devices if device.id == "auto")
    resolved = _auto_device(devices) if selected.id == "auto" else selected
    return {
        "requested": requested,
        "resolved": resolved.id,
        "label": resolved.label,
        "accelerator": resolved.accelerator,
        "devices": resolved.devices,
        "available": resolved.available,
        "reason": resolved.reason,
    }


def compute_metadata_from_trainer_kwargs(model_kwargs: dict[str, Any]) -> dict[str, Any]:
    """Describe compute settings already attached to a NeuralForecast model."""
    accelerator = str(model_kwargs.get("accelerator") or "auto")
    devices = model_kwargs.get("devices")
    label = accelerator.upper()
    resolved = accelerator
    if accelerator == "gpu" and isinstance(devices, list) and devices:
        resolved = f"cuda:{devices[0]}"
        label = _device_label(resolved, f"GPU CUDA {devices[0]}")
    elif accelerator == "mps":
        resolved = "mps"
        label = "GPU Apple Metal (MPS)"
    elif accelerator == "cpu":
        resolved = "cpu"
        label = "CPU"
    return {
        "requested": resolved,
        "resolved": resolved,
        "label": label,
        "accelerator": accelerator,
        "devices": devices,
    }


def _device_label(device_id: str, fallback: str) -> str:
    return next(
        (device.label for device in available_compute_devices() if device.id == device_id),
        fallback,
    )


def _torch_accelerator_info() -> dict[str, Any]:
    try:
        import torch
    except ImportError:
        return {
            "torch": None,
            "torch_version": None,
            "cuda_build": None,
            "cuda_available": False,
            "cuda_device_count": 0,
            "mps_available": False,
        }

    mps_backend = getattr(torch.backends, "mps", None)
    return {
        "torch": torch,
        "torch_version": torch.__version__,
        "cuda_build": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "mps_available": bool(mps_backend is not None and mps_backend.is_available()),
    }


def _nvidia_smi_gpus() -> list[tuple[int, str]]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            check=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return []

    gpus: list[tuple[int, str]] = []
    for line in result.stdout.splitlines():
        parts = [part.strip() for part in line.split(",", maxsplit=1)]
        if len(parts) != 2:
            continue
        try:
            index = int(parts[0])
        except ValueError:
            continue
        gpus.append((index, parts[1]))
    return gpus


def _cuda_unavailable_reason(torch_info: dict[str, Any]) -> str:
    if torch_info.get("torch") is None:
        return "PyTorch no esta instalado en este entorno."
    version = torch_info.get("torch_version") or "desconocida"
    if torch_info.get("cuda_build") is None:
        return f"PyTorch {version} esta instalado en variante CPU-only; instala PyTorch con CUDA."
    return "PyTorch no puede inicializar CUDA aunque Windows detecta una GPU NVIDIA."


def _auto_device(devices: list[ComputeDevice]) -> ComputeDevice:
    return next(
        (
            device
            for device in devices
            if device.id not in {"auto", "cpu"} and device.available
        ),
        next(device for device in devices if device.id == "cpu"),
    )
