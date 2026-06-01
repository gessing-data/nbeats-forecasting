from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules, copy_metadata


hiddenimports = (
    collect_submodules("ray._private")
    + collect_submodules("ray.air")
    + collect_submodules("ray.train")
    + collect_submodules("ray.tune")
)

datas = collect_data_files("ray") + copy_metadata("ray")
binaries = collect_dynamic_libs("ray")
