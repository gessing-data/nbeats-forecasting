from energy_forecast.app_paths import prepare_workspace
from energy_forecast.services import dataset_seeding


def test_service_emits_progress_and_updates_settings(monkeypatch, tmp_path) -> None:
    paths = prepare_workspace(tmp_path)
    phases: list[str] = []

    class FakeSeeder:
        def __init__(self, _paths, progress=None) -> None:
            self.progress = progress

        def install(self) -> list[str]:
            self.progress("preparing_workspace", "Preparando")
            return ["AT"]

    monkeypatch.setattr(dataset_seeding, "OpsdSeeder", FakeSeeder)

    result = dataset_seeding.install_datasets(paths, lambda phase, _message: phases.append(phase))

    assert result.ok
    assert phases == ["preparing_workspace", "updating_settings"]
