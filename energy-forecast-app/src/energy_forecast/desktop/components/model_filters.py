import flet as ft

from energy_forecast.desktop.model_catalog import ModelRecord


SelectionState = dict[str, str]

HORIZON_OPTIONS = [24, 48, 168]
INPUT_SIZE_OPTIONS = [168, 336, 720]
FREQUENCY_OPTIONS = ["h"]
MAX_STEPS_OPTIONS = [100]


def filter_models(
    models: list[ModelRecord],
    query: str,
    zone: str,
    horizon: str,
    input_size: str,
    frequency: str,
    max_steps: str,
) -> list[ModelRecord]:
    query_terms = _normalize(query).split()
    filtered = []

    for model in models:
        searchable = _searchable_text(model)
        if query_terms and not all(term in searchable for term in query_terms):
            continue
        if zone and model["zone_code"] != zone:
            continue
        if horizon and str(model["horizon"]) != horizon:
            continue
        if input_size and str(model["input_size"]) != input_size:
            continue
        if frequency and str(model["frequency"]) != frequency:
            continue
        if max_steps and str(model["max_steps"]) != max_steps:
            continue
        filtered.append(model)

    return filtered


def build_filter_button() -> ft.IconButton:
    return ft.IconButton(
        icon=ft.Icons.TUNE,
        icon_color="#334155",
        tooltip="Filtros",
        width=48,
        height=48,
    )


def update_filter_badge(filter_button: ft.IconButton, state: SelectionState) -> None:
    filters_active = any(
        state.get(key, "")
        for key in ("zone", "horizon", "input_size", "frequency", "max_steps")
    )
    filter_button.badge = "" if filters_active else None


def build_filters_dialog(
    page: ft.Page,
    models: list[ModelRecord],
    state: SelectionState,
    on_apply: ft.EventHandler,
    on_clear: ft.EventHandler,
) -> ft.AlertDialog:
    zone_filter = _zone_filter(models, state)
    horizon_filter = _horizon_filter(state)
    input_size_filter = _input_size_filter(state)
    frequency_filter = _frequency_filter(state)
    max_steps_filter = _max_steps_filter(state)

    def close_filters(_: ft.ControlEvent | None = None) -> None:
        page.pop_dialog()

    def apply_filters(event: ft.ControlEvent) -> None:
        state["zone"] = zone_filter.value or ""
        state["horizon"] = horizon_filter.value or ""
        state["input_size"] = input_size_filter.value or ""
        state["frequency"] = frequency_filter.value or ""
        state["max_steps"] = max_steps_filter.value or ""
        page.pop_dialog()
        on_apply(event)

    def clear_filters(event: ft.ControlEvent) -> None:
        zone_filter.value = ""
        horizon_filter.value = ""
        input_size_filter.value = ""
        frequency_filter.value = ""
        max_steps_filter.value = ""
        state["zone"] = ""
        state["horizon"] = ""
        state["input_size"] = ""
        state["frequency"] = ""
        state["max_steps"] = ""
        page.pop_dialog()
        on_clear(event)

    return ft.AlertDialog(
        modal=True,
        bgcolor=ft.Colors.WHITE,
        elevation=0,
        barrier_color="#0F172A66",
        shape=ft.RoundedRectangleBorder(radius=18),
        title_padding=ft.Padding(24, 24, 24, 4),
        content_padding=ft.Padding(24, 8, 24, 8),
        actions_padding=ft.Padding(16, 4, 16, 16),
        title=_dialog_title(),
        content=_dialog_content(
            controls=[
                zone_filter,
                horizon_filter,
                input_size_filter,
                frequency_filter,
                max_steps_filter,
            ]
        ),
        actions=[
            _dialog_action("Limpiar", clear_filters),
            _dialog_action("Cancelar", close_filters),
            _dialog_action("Aplicar", apply_filters),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )


def _zone_filter(models: list[ModelRecord], state: SelectionState) -> ft.Dropdown:
    return _dropdown(
        label="Zona",
        options=_zone_options(models),
        value=state.get("zone", ""),
    )


def _zone_options(models: list[ModelRecord]) -> list[ft.dropdown.Option]:
    zones = sorted(
        {
            (str(model.get("zone_code", "")), str(model.get("zone", "")))
            for model in models
            if model.get("zone_code")
        },
        key=lambda zone: zone[1].lower(),
    )
    return [ft.dropdown.Option("", "Todas")] + [
        ft.dropdown.Option(code, f"{name} ({code})") for code, name in zones
    ]


def _horizon_filter(state: SelectionState) -> ft.Dropdown:
    return _dropdown(
        label="Horizonte",
        options=_dropdown_options(HORIZON_OPTIONS, "Todos"),
        value=state.get("horizon", ""),
    )


def _input_size_filter(state: SelectionState) -> ft.Dropdown:
    return _dropdown(
        label="Input size",
        options=_dropdown_options(INPUT_SIZE_OPTIONS, "Todos"),
        value=state.get("input_size", ""),
    )


def _frequency_filter(state: SelectionState) -> ft.Dropdown:
    return _dropdown(
        label="Frecuencia",
        options=_dropdown_options(FREQUENCY_OPTIONS, "Todas"),
        value=state.get("frequency", ""),
    )


def _max_steps_filter(state: SelectionState) -> ft.Dropdown:
    return _dropdown(
        label="Max steps",
        options=_dropdown_options(MAX_STEPS_OPTIONS, "Todos"),
        value=state.get("max_steps", ""),
    )


def _searchable_text(model: ModelRecord) -> str:
    metadata = model.get("metadata", {})
    values = [
        model.get("name", ""),
        model.get("description", ""),
        model.get("zone", ""),
        model.get("zone_code", ""),
        model.get("dataset", ""),
        model.get("model_type", ""),
        model.get("frequency", ""),
        model.get("horizon", ""),
        model.get("input_size", ""),
        model.get("max_steps", ""),
    ]
    if isinstance(metadata, dict):
        values.extend(
            [
                metadata.get("selection_mode", ""),
                metadata.get("source_file", ""),
                metadata.get("logs_path", ""),
            ]
        )
    return _normalize(" ".join(str(value) for value in values))


def _normalize(value: str) -> str:
    return value.strip().lower()


def _dialog_title() -> ft.Row:
    return ft.Row(
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.Icons.TUNE, size=20, color="#334155"),
            ft.Text("Filtros", weight=ft.FontWeight.W_600, color="#0F172A", size=20),
        ],
    )


def _dialog_content(controls: list[ft.Control]) -> ft.Container:
    return ft.Container(
        width=360,
        content=ft.Column(
            tight=True,
            spacing=14,
            controls=controls,
        ),
    )


def _dropdown(label: str, options: list[ft.dropdown.Option], value: str) -> ft.Dropdown:
    return ft.Dropdown(
        color="#334155",
        label=label,
        options=options,
        value=value,
    )


def _dropdown_options(values: list[str | int], label: str) -> list[ft.dropdown.Option]:
    return [ft.dropdown.Option("", label)] + [
        ft.dropdown.Option(str(value), str(value)) for value in values
    ]


def _dialog_action(
    label: str, on_click: ft.EventHandler, color: str = "#0F172A"
) -> ft.TextButton:
    return ft.TextButton(
        label,
        style=ft.ButtonStyle(color=color),
        on_click=on_click,
    )
