from __future__ import annotations

import pytest

from energy_forecast.models import compute


def teardown_function() -> None:
    compute.available_compute_devices.cache_clear()


def test_lists_nvidia_gpu_as_unavailable_when_torch_is_cpu_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        compute,
        "_torch_accelerator_info",
        lambda: {
            "torch": object(),
            "torch_version": "2.10.0+cpu",
            "cuda_build": None,
            "cuda_available": False,
            "cuda_device_count": 0,
            "mps_available": False,
        },
    )
    monkeypatch.setattr(
        compute,
        "_nvidia_smi_gpus",
        lambda: [(0, "NVIDIA GeForce RTX 3050 Laptop GPU")],
    )

    devices = compute.available_compute_devices()

    assert [device.id for device in devices] == ["auto", "cpu", "unavailable:cuda:0"]
    unavailable = devices[-1]
    assert unavailable.label == "GPU 0: NVIDIA GeForce RTX 3050 Laptop GPU (no disponible para PyTorch)"
    assert unavailable.available is False
    assert "CPU-only" in unavailable.reason


def test_unavailable_gpu_selection_fails_with_actionable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        compute,
        "_torch_accelerator_info",
        lambda: {
            "torch": object(),
            "torch_version": "2.10.0+cpu",
            "cuda_build": None,
            "cuda_available": False,
            "cuda_device_count": 0,
            "mps_available": False,
        },
    )
    monkeypatch.setattr(compute, "_nvidia_smi_gpus", lambda: [(0, "NVIDIA GPU")])

    with pytest.raises(RuntimeError, match="PyTorch 2.10.0\\+cpu"):
        compute.compute_trainer_kwargs("unavailable:cuda:0")


def test_auto_uses_cuda_when_pytorch_can_use_gpu(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCuda:
        @staticmethod
        def get_device_name(index: int) -> str:
            return "NVIDIA GPU"

    class FakeTorch:
        cuda = FakeCuda()

    monkeypatch.setattr(
        compute,
        "_torch_accelerator_info",
        lambda: {
            "torch": FakeTorch(),
            "torch_version": "2.10.0+cu130",
            "cuda_build": "13.0",
            "cuda_available": True,
            "cuda_device_count": 1,
            "mps_available": False,
        },
    )
    monkeypatch.setattr(compute, "_nvidia_smi_gpus", lambda: [(0, "NVIDIA GPU")])

    assert compute.compute_trainer_kwargs("auto") == {"accelerator": "gpu", "devices": [0]}
