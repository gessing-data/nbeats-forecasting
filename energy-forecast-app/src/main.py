import sys

from energy_forecast.desktop.app import run_app


def _packaging_smoke_test() -> None:
    from energy_forecast.models.nbeats_model import NBeatsModel
    from neuralforecast import NeuralForecast
    from neuralforecast.models import NBEATS

    import ray

    assert NBeatsModel
    assert NeuralForecast
    assert NBEATS
    assert ray


# Flet CLI expects this file when using [tool.flet.app] path = "src".
if __name__ == "__main__":
    if "--packaging-smoke-test" in sys.argv:
        _packaging_smoke_test()
        raise SystemExit(0)

    run_app()
