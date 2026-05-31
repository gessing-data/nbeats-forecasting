from energy_forecast.app_paths import default_settings, prepare_workspace, load_settings, save_settings
from energy_forecast.seeders.workspace_reset import reinstall_workspace


def test_workspace_reset_preserves_settings_and_resets_seeds(tmp_path) -> None:
    paths = prepare_workspace(tmp_path)
    paths.imported_data_dir.joinpath("user.csv").write_text("x\n", encoding="utf-8")
    paths.models_dir.joinpath("model").mkdir()
    settings = load_settings(paths)
    settings["theme"] = "dark"
    settings["seeds"]["initialized"] = True
    save_settings(paths, settings)

    reinstall_workspace(paths)

    updated = load_settings(paths)
    assert updated["theme"] == "dark"
    assert updated["seeds"] == default_settings()["seeds"]
    assert not paths.imported_data_dir.joinpath("user.csv").exists()
    assert not paths.models_dir.joinpath("model").exists()
