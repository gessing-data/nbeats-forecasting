from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import flet as ft
import pandas as pd

from energy_forecast.app_paths import AppPaths
from energy_forecast.storage import safe_artifact_name


BACKGROUND_COLOR = "#F8FAFC"
BORDER_COLOR = "#E2E8F0"
PRIMARY_TEXT = "#0F172A"
SECONDARY_TEXT = "#64748B"
MAX_CONTENT_WIDTH = 920
PAGE_PADDING = 24


@dataclass(frozen=True)
class DatasetInfo:
    name: str
    path: Path
    origin: str
    rows: int
    date_range: str
    valid: bool
    error: str = ""


def build_model_creation_page(
    page: ft.Page,
    paths: AppPaths,
    on_create: Any | None = None,
    on_success: ft.ControlEventHandler | None = None,
) -> ft.Control:
    processed_data_root = paths.processed_data_dir
    imported_data_root = paths.imported_data_dir
    state: dict[str, Any] = {
        "datasets": [],
        "selected": None,
        "training": False,
        "timestamps": [],
        "hours_by_date": {},
        "range_start": None,
        "range_end": None,
    }
    dataset_list = ft.Column(spacing=10)
    preview = ft.Container()
    selection_fields = ft.Container()
    error = _error_message()
    loading = ft.ProgressRing(width=18, height=18, visible=False)

    title = _styled_text_field(
        label="Titulo del modelo",
        value=f"{int(time.time())}_model",
        width=float("inf"),
    )
    description = _styled_text_field(
        label="Descripcion opcional",
        value="",
        width=float("inf"),
        multiline=True,
        min_lines=2,
        max_lines=4,
    )
    freq = _text_field("Frecuencia", "h")
    horizon = _text_field("Horizonte", "24")
    input_size = _text_field("Input size", "168")
    max_steps = _text_field("Max steps", "100")
    selection_mode = _dropdown(
        "Modo de seleccion",
        [
            ft.dropdown.Option("all", "Usar todo el dataset"),
            ft.dropdown.Option("first_n", "Primeras N filas"),
            ft.dropdown.Option("row_range", "Rango de filas"),
            ft.dropdown.Option("date_range", "Rango de fecha y hora"),
        ],
        "all",
    )
    first_n = _text_field("Primeras N filas", "")
    start_row = _text_field("Fila inicial", "")
    end_row = _text_field("Fila final", "")
    start_hour = _dropdown("Hora inicial", [], "")
    end_hour = _dropdown("Hora final", [], "")
    date_range_picker = ft.DateRangePicker(
        confirm_text="Aplicar",
        cancel_text="Cancelar",
        help_text="Selecciona el rango de fechas",
        entry_mode=ft.DatePickerEntryMode.CALENDAR,
    )
    date_range_summary = ft.Text(
        "Selecciona un dataset y un rango de fechas.", size=13, color=SECONDARY_TEXT
    )

    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    def refresh_datasets() -> None:
        state["datasets"] = _load_datasets(processed_data_root, imported_data_root)
        selected = state.get("selected")
        if selected and not any(
            item.path == selected.path for item in state["datasets"]
        ):
            state["selected"] = None
        render_datasets()
        render_preview()

    def select_dataset(dataset: DatasetInfo) -> None:
        state["selected"] = dataset
        _prepare_temporal_state(state, dataset)
        _configure_date_range_picker(date_range_picker, state)
        update_selection_fields()
        error.visible = False
        render_datasets()
        render_preview()
        page.update()

    def render_datasets() -> None:
        processed = [item for item in state["datasets"] if item.origin == "Aplicacion"]
        imported = [item for item in state["datasets"] if item.origin == "Importado"]
        dataset_list.controls = [
            _dataset_group(
                "Datasets de la aplicacion", processed, select_dataset, state
            ),
            _dataset_group("Datasets importados", imported, select_dataset, state),
        ]

    def render_preview() -> None:
        dataset = state.get("selected")
        preview.content = _dataset_preview(dataset)

    def open_date_range(_: ft.ControlEvent) -> None:
        if state.get("selected") is None:
            _show_error(error, "Selecciona un dataset antes de elegir fechas.", page)
            return
        date_range_picker.open = True
        page.update()

    def refresh_hours() -> None:
        start_date = state.get("range_start")
        end_date = state.get("range_end")
        hours_by_date: dict[date, list[str]] = state.get("hours_by_date", {})
        start_options = hours_by_date.get(start_date, []) if start_date else []
        end_options = hours_by_date.get(end_date, []) if end_date else []
        start_hour.options = _option_list(start_options)
        end_hour.options = _option_list(end_options)
        start_hour.value = start_options[0] if start_options else ""
        end_hour.value = end_options[-1] if end_options else ""
        date_range_summary.value = _date_range_label(
            state, start_hour.value, end_hour.value
        )

    def on_date_range_change(_: ft.ControlEvent) -> None:
        if date_range_picker.start_value is not None:
            state["range_start"] = _as_date(date_range_picker.start_value)
        if date_range_picker.end_value is not None:
            state["range_end"] = _as_date(date_range_picker.end_value)
        refresh_hours()
        page.update()

    def on_hour_change(_: ft.ControlEvent) -> None:
        date_range_summary.value = _date_range_label(
            state, start_hour.value, end_hour.value
        )
        page.update()

    def update_selection_fields(_: ft.ControlEvent | None = None) -> None:
        mode = selection_mode.value or "all"
        _reset_inactive_selection_values(mode, first_n, start_row, end_row)
        date_range_picker.open = False
        selection_fields.content = None
        controls: list[ft.Control] = []
        if mode == "first_n":
            controls = [_col(first_n, lg=4)]
        elif mode == "row_range":
            controls = [_col(start_row, lg=4), _col(end_row, lg=4)]
        elif mode == "date_range":
            refresh_hours()
            controls = [
                ft.Container(
                    col={"sm": 12},
                    content=ft.Row(
                        wrap=True,
                        spacing=12,
                        run_spacing=8,
                        controls=[
                            ft.OutlinedButton(
                                "Seleccionar rango",
                                icon=ft.Icons.DATE_RANGE,
                                on_click=open_date_range,
                            ),
                            date_range_summary,
                        ],
                    ),
                ),
                _col(start_hour, lg=4),
                _col(end_hour, lg=4),
                date_range_picker,
            ]
        selection_fields.content = ft.ResponsiveRow(run_spacing=12, controls=controls)
        if _ is not None:
            page.update()

    selection_mode.on_select = update_selection_fields
    date_range_picker.on_change = on_date_range_change
    start_hour.on_select = on_hour_change
    end_hour.on_select = on_hour_change

    def import_file(source: Path) -> None:
        try:
            imported_path = _import_dataset(source, imported_data_root)
        except Exception as exc:  # noqa: BLE001 - UI must surface validation failures.
            _show_error(error, str(exc), page)
            return

        refresh_datasets()
        state["selected"] = next(
            (item for item in state["datasets"] if item.path == imported_path), None
        )
        if state["selected"] is not None:
            _prepare_temporal_state(state, state["selected"])
            _configure_date_range_picker(date_range_picker, state)
            update_selection_fields()
        render_datasets()
        render_preview()
        error.visible = False
        page.update()

    async def open_import(_: ft.ControlEvent) -> None:
        files = await file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["csv"],
            dialog_title="Importar dataset CSV",
        )
        if files:
            import_file(Path(files[0].path or ""))

    def create_model(_: ft.ControlEvent) -> None:
        if state["training"]:
            return
        dataset = state.get("selected")
        try:
            if dataset is None:
                raise ValueError("Selecciona un dataset antes de crear el modelo.")
            args = _training_args(
                freq=freq.value,
                horizon=horizon.value,
                input_size=input_size.value,
                max_steps=max_steps.value,
                selection_mode=selection_mode.value or "all",
                first_n=first_n.value,
                start_row=start_row.value,
                end_row=end_row.value,
                start_timestamp=_selected_timestamp(
                    state.get("range_start"), start_hour.value
                ),
                end_timestamp=_selected_timestamp(
                    state.get("range_end"), end_hour.value
                ),
            )
            request = {
                "title": _required_text(title.value, "Titulo del modelo"),
                "dataset_name": dataset.name,
                "source_file": dataset.path,
                "description": (description.value or "").strip(),
                **args,
            }
            if on_create is None:
                raise RuntimeError("El flujo de entrenamiento no esta configurado.")
            state["training"] = True
            loading.visible = True
            error.visible = False
            page.update()
            on_create(request)
        except Exception as exc:  # noqa: BLE001 - UI must keep the user on the form.
            state["training"] = False
            loading.visible = False
            _show_error(error, str(exc), page)
            return

        if on_success is not None:
            on_success(None)

    refresh_datasets()
    update_selection_fields()

    return _page_shell(
        ft.Column(
            spacing=18,
            controls=[
                _page_header(),
                _metadata_section(title, description),
                _training_config_section(freq, horizon, input_size, max_steps),
                _dataset_section(dataset_list, open_import),
                preview,
                _selection_mode_section(
                    selection_mode,
                    selection_fields,
                ),
                error,
                _form_actions(page, create_model, loading),
            ],
        )
    )


def _load_datasets(processed_data_root: Path, imported_data_root: Path) -> list[DatasetInfo]:
    datasets: list[DatasetInfo] = []
    for root, origin in (
        (processed_data_root, "Aplicacion"),
        (imported_data_root, "Importado"),
    ):
        if not root.exists():
            continue
        datasets.extend(
            _dataset_info(path, origin) for path in sorted(root.glob("*.csv"))
        )
    return datasets


def _dataset_info(path: Path, origin: str) -> DatasetInfo:
    try:
        df = _validated_dataset(path)
        start = df["timestamp"].min()
        end = df["timestamp"].max()
        date_range = (
            f"{start} - {end}" if pd.notna(start) and pd.notna(end) else "Sin rango"
        )
        return DatasetInfo(path.stem, path, origin, len(df), date_range, True)
    except Exception as exc:  # noqa: BLE001 - invalid datasets are visible but not selectable.
        return DatasetInfo(path.stem, path, origin, 0, "Sin rango", False, str(exc))


def _validated_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise ValueError("El archivo seleccionado no existe.")
    df = pd.read_csv(path)
    missing = {"timestamp", "y"}.difference(df.columns)
    if missing:
        raise ValueError("El CSV debe incluir las columnas timestamp,y.")
    prepared = df.loc[:, ["timestamp", "y"]].copy()
    prepared["timestamp"] = pd.to_datetime(
        prepared["timestamp"], errors="coerce", utc=True
    )
    prepared["y"] = pd.to_numeric(prepared["y"], errors="coerce")
    prepared = prepared.dropna(subset=["timestamp", "y"])
    if prepared.empty:
        raise ValueError("El CSV debe incluir al menos una fila util.")
    prepared = prepared.sort_values("timestamp").reset_index(drop=True)
    _validate_temporal_continuity(prepared)
    return prepared


def _validate_temporal_continuity(df: pd.DataFrame) -> None:
    if df["timestamp"].duplicated().any():
        raise ValueError("El CSV contiene timestamps duplicados.")
    if len(df) < 2:
        return

    deltas = df["timestamp"].diff().dropna()
    expected = deltas.iloc[0]
    if expected <= pd.Timedelta(0):
        raise ValueError("El CSV debe estar ordenado con timestamps crecientes.")
    if not (deltas == expected).all():
        raise ValueError(
            f"El CSV contiene huecos temporales; se esperaba una frecuencia constante de {_format_timedelta(expected)}."
        )


def _format_timedelta(value: pd.Timedelta) -> str:
    seconds = int(value.total_seconds())
    if seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    if seconds % 60 == 0:
        return f"{seconds // 60}min"
    return f"{seconds}s"


def _import_dataset(source: Path, imported_data_root: Path) -> Path:
    df = _validated_dataset(source)
    imported_data_root.mkdir(parents=True, exist_ok=True)
    target = imported_data_root / f"{safe_artifact_name(source.stem)}.csv"
    counter = 2
    while target.exists():
        target = imported_data_root / f"{safe_artifact_name(source.stem)}-{counter}.csv"
        counter += 1
    shutil.copy2(source, target)
    return target


def _training_args(**values: str) -> dict[str, Any]:
    mode = values["selection_mode"]
    selection_metadata: dict[str, Any] = {}
    if mode == "first_n":
        selection_metadata["first_n"] = _positive_int(
            values["first_n"], "Primeras N filas"
        )
    elif mode == "row_range":
        selection_metadata["start_row"] = _non_negative_int(
            values["start_row"], "Fila inicial"
        )
        selection_metadata["end_row"] = _positive_int(values["end_row"], "Fila final")
        if selection_metadata["end_row"] <= selection_metadata["start_row"]:
            raise ValueError("El rango debe cumplir 0 <= fila inicial < fila final.")
    elif mode == "date_range":
        start = (values["start_timestamp"] or "").strip()
        end = (values["end_timestamp"] or "").strip()
        if not start or not end:
            raise ValueError("El rango de fecha requiere fecha inicial y final.")
        if pd.to_datetime(end, utc=True) < pd.to_datetime(start, utc=True):
            raise ValueError(
                "La fecha final debe ser mayor o igual a la fecha inicial."
            )
        selection_metadata.update({"start_timestamp": start, "end_timestamp": end})
    return {
        "freq": (values["freq"] or "h").strip(),
        "horizon": _positive_int(values["horizon"], "Horizonte"),
        "input_size": _positive_int(values["input_size"], "Input size"),
        "max_steps": _positive_int(values["max_steps"], "Max steps"),
        "selection_mode": mode,
        "selection_metadata": selection_metadata,
    }


def _positive_int(value: str, label: str) -> int:
    try:
        parsed = int((value or "").strip())
    except ValueError as exc:
        raise ValueError(f"{label} debe ser un entero.") from exc
    if parsed <= 0:
        raise ValueError(f"{label} debe ser mayor que cero.")
    return parsed


def _non_negative_int(value: str, label: str) -> int:
    try:
        parsed = int((value or "").strip())
    except ValueError as exc:
        raise ValueError(f"{label} debe ser un entero.") from exc
    if parsed < 0:
        raise ValueError(f"{label} debe ser mayor o igual a cero.")
    return parsed


def _page_shell(content: ft.Control) -> ft.Container:
    return ft.Container(
        expand=True,
        bgcolor=BACKGROUND_COLOR,
        alignment=ft.Alignment(0, -1),
        content=ft.Container(
            width=MAX_CONTENT_WIDTH + (PAGE_PADDING * 2),
            padding=ft.Padding(PAGE_PADDING, 28, PAGE_PADDING, 28),
            content=content,
        ),
    )


def _page_header() -> ft.Column:
    return ft.Column(
        spacing=8,
        controls=[
            ft.Text(
                "Crear modelo N-BEATS",
                size=28,
                weight=ft.FontWeight.W_600,
                color=PRIMARY_TEXT,
            ),
            ft.Text(
                "Selecciona un dataset timestamp,y, ajusta los parametros y entrena un nuevo artefacto.",
                size=14,
                color=SECONDARY_TEXT,
            ),
        ],
    )


def _dataset_section(
    dataset_list: ft.Column, on_import: ft.ControlEventHandler
) -> ft.Container:
    return _card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            "Dataset",
                            size=18,
                            weight=ft.FontWeight.W_600,
                            color=PRIMARY_TEXT,
                        ),
                        ft.OutlinedButton(
                            "Importar CSV",
                            icon=ft.Icons.UPLOAD_FILE,
                            on_click=on_import,
                        ),
                    ],
                ),
                dataset_list,
            ],
        )
    )


def _dataset_group(
    title: str, datasets: list[DatasetInfo], on_select: Any, state: dict[str, Any]
) -> ft.Column:
    selected = state.get("selected")
    controls: list[ft.Control] = [
        ft.Text(title, size=13, weight=ft.FontWeight.W_600, color=SECONDARY_TEXT)
    ]
    if not datasets:
        controls.append(
            ft.Text("No hay datasets disponibles.", size=13, color=SECONDARY_TEXT)
        )
    else:
        controls.extend(_dataset_card(item, selected, on_select) for item in datasets)
    return ft.Column(spacing=8, controls=controls)


def _dataset_card(
    dataset: DatasetInfo, selected: DatasetInfo | None, on_select: Any
) -> ft.Container:
    is_selected = selected is not None and selected.path == dataset.path
    return ft.Container(
        width=float("inf"),
        border=_border("#334155" if is_selected else BORDER_COLOR),
        border_radius=12,
        bgcolor="#F8FAFC" if is_selected else ft.Colors.WHITE,
        padding=14,
        ink=dataset.valid,
        on_click=(lambda _: on_select(dataset)) if dataset.valid else None,
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Text(
                    dataset.name,
                    size=15,
                    weight=ft.FontWeight.W_600,
                    color=PRIMARY_TEXT,
                ),
                ft.Text(
                    f"{dataset.origin} | {dataset.rows} filas | {dataset.date_range}",
                    size=12,
                    color=SECONDARY_TEXT,
                ),
                ft.Text(
                    "Valido" if dataset.valid else f"Invalido: {dataset.error}",
                    size=12,
                    color="#16A34A" if dataset.valid else "#DC2626",
                ),
            ],
        ),
    )


def _dataset_preview(dataset: DatasetInfo | None) -> ft.Container:
    if dataset is None:
        return _card(
            ft.Text(
                "Selecciona un dataset para ver una vista previa.",
                size=13,
                color=SECONDARY_TEXT,
            )
        )
    df = _validated_dataset(dataset.path).head(8)
    rows = [
        ft.DataRow(
            cells=[
                ft.DataCell(
                    ft.Text(_format_timestamp(row.timestamp), color=PRIMARY_TEXT)
                ),
                ft.DataCell(ft.Text(str(row.y), color=PRIMARY_TEXT)),
            ]
        )
        for row in df.itertuples()
    ]
    return _card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text(
                    "Vista previa",
                    size=18,
                    weight=ft.FontWeight.W_600,
                    color=PRIMARY_TEXT,
                ),
                ft.Row(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.DataTable(
                            columns=[
                                ft.DataColumn(
                                    ft.Text(
                                        "timestamp",
                                        color=PRIMARY_TEXT,
                                        weight=ft.FontWeight.W_600,
                                    )
                                ),
                                ft.DataColumn(
                                    ft.Text(
                                        "y",
                                        color=PRIMARY_TEXT,
                                        weight=ft.FontWeight.W_600,
                                    )
                                ),
                            ],
                            rows=rows,
                            border=_border("#CBD5E1"),
                            border_radius=12,
                            heading_row_color="#F1F5F9",
                            data_row_color=ft.Colors.WHITE,
                            heading_text_style=ft.TextStyle(
                                color=PRIMARY_TEXT, weight=ft.FontWeight.W_600
                            ),
                            data_text_style=ft.TextStyle(color=PRIMARY_TEXT),
                            horizontal_lines=ft.BorderSide(1, "#E2E8F0"),
                            column_spacing=40,
                        )
                    ],
                ),
            ],
        )
    )


def _training_config_section(
    freq: ft.TextField,
    horizon: ft.TextField,
    input_size: ft.TextField,
    max_steps: ft.TextField,
) -> ft.Container:
    return _card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text(
                    "Configuracion N-BEATS",
                    size=18,
                    weight=ft.FontWeight.W_600,
                    color=PRIMARY_TEXT,
                ),
                ft.ResponsiveRow(
                    controls=[
                        _col(freq),
                        _col(horizon),
                        _col(input_size),
                        _col(max_steps),
                    ]
                ),
            ],
        )
    )


def _selection_mode_section(
    selection_mode: ft.Dropdown, selection_fields: ft.Container
) -> ft.Container:
    return _card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text(
                    "Seleccion de filas",
                    size=18,
                    weight=ft.FontWeight.W_600,
                    color=PRIMARY_TEXT,
                ),
                ft.ResponsiveRow(run_spacing=12, controls=[_col(selection_mode, lg=4)]),
                selection_fields,
            ],
        )
    )


def _metadata_section(title: ft.TextField, description: ft.TextField) -> ft.Container:
    return _card(
        ft.Column(
            spacing=12,
            controls=[
                ft.Text(
                    "Metadata", size=18, weight=ft.FontWeight.W_600, color=PRIMARY_TEXT
                ),
                ft.Container(width=float("inf"), content=title),
                ft.Container(width=float("inf"), content=description),
            ],
        )
    )


def _form_actions(
    page: ft.Page, on_create: ft.ControlEventHandler, loading: ft.ProgressRing
) -> ft.Row:
    return ft.Row(
        alignment=ft.MainAxisAlignment.END,
        controls=[
            loading,
            ft.TextButton("Cancelar", on_click=lambda _: page.navigate("/")),
            ft.FilledButton("Crear modelo", on_click=on_create),
        ],
    )


def _error_message() -> ft.Text:
    return ft.Text("", size=13, color="#DC2626", visible=False)


def _show_error(control: ft.Text, message: str, page: ft.Page) -> None:
    control.value = message
    control.visible = True
    page.update()


def _required_text(value: str | None, label: str) -> str:
    clean = (value or "").strip()
    if not clean:
        raise ValueError(f"{label} es obligatorio.")
    return clean


def _reset_inactive_selection_values(
    mode: str,
    first_n: ft.TextField,
    start_row: ft.TextField,
    end_row: ft.TextField,
) -> None:
    if mode != "first_n":
        first_n.value = ""
    if mode != "row_range":
        start_row.value = ""
        end_row.value = ""


def _prepare_temporal_state(state: dict[str, Any], dataset: DatasetInfo) -> None:
    df = _validated_dataset(dataset.path)
    timestamps = list(df["timestamp"])
    hours_by_date: dict[date, list[str]] = {}
    for timestamp in timestamps:
        timestamp_date = timestamp.date()
        hours_by_date.setdefault(timestamp_date, []).append(timestamp.strftime("%H:%M"))
    state["timestamps"] = timestamps
    state["hours_by_date"] = hours_by_date
    state["range_start"] = timestamps[0].date()
    state["range_end"] = timestamps[-1].date()


def _configure_date_range_picker(
    date_range_picker: ft.DateRangePicker, state: dict[str, Any]
) -> None:
    timestamps = state.get("timestamps") or []
    if not timestamps:
        return
    first_date = timestamps[0].date()
    last_date = timestamps[-1].date()
    date_range_picker.first_date = first_date
    date_range_picker.last_date = last_date
    date_range_picker.current_date = first_date
    date_range_picker.start_value = first_date
    date_range_picker.end_value = last_date


def _as_date(value: date | datetime | pd.Timestamp) -> date:
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, datetime):
        return value.date()
    return value


def _option_list(values: list[str]) -> list[ft.dropdown.Option]:
    return [ft.dropdown.Option(value, value) for value in values]


def _selected_timestamp(selected_date: date | None, selected_hour: str | None) -> str:
    if selected_date is None or not selected_hour:
        return ""
    return f"{selected_date.isoformat()} {selected_hour}:00+00:00"


def _date_range_label(
    state: dict[str, Any], start_hour: str | None, end_hour: str | None
) -> str:
    start_date = state.get("range_start")
    end_date = state.get("range_end")
    if start_date is None or end_date is None or not start_hour or not end_hour:
        return "Selecciona un rango de fechas para cargar horas disponibles."
    return f"Rango: {start_date.isoformat()} {start_hour} UTC - {end_date.isoformat()} {end_hour} UTC"


def _format_timestamp(value: pd.Timestamp) -> str:
    return value.strftime("%Y-%m-%d %H:%M UTC")


def _text_field(label: str, value: str) -> ft.TextField:
    return _styled_text_field(label=label, value=value)


def _styled_text_field(label: str, value: str, **kwargs: Any) -> ft.TextField:
    return ft.TextField(
        label=label,
        value=value,
        color=PRIMARY_TEXT,
        label_style=ft.TextStyle(color=SECONDARY_TEXT),
        hint_style=ft.TextStyle(color=SECONDARY_TEXT),
        border_color="#CBD5E1",
        focused_border_color="#334155",
        cursor_color=PRIMARY_TEXT,
        **kwargs,
    )


def _dropdown(label: str, options: list[ft.dropdown.Option], value: str) -> ft.Dropdown:
    return ft.Dropdown(
        label=label,
        options=options,
        value=value,
        color=PRIMARY_TEXT,
        label_style=ft.TextStyle(color=SECONDARY_TEXT),
        hint_style=ft.TextStyle(color=SECONDARY_TEXT),
        border_color="#CBD5E1",
        focused_border_color="#334155",
    )


def _col(control: ft.Control, *, lg: int = 3) -> ft.Container:
    return ft.Container(col={"sm": 12, "md": 6, "lg": lg}, content=control)


def _card(content: ft.Control) -> ft.Container:
    return ft.Container(
        width=float("inf"),
        bgcolor=ft.Colors.WHITE,
        border=_border(),
        border_radius=16,
        padding=18,
        content=content,
    )


def _border(color: str = BORDER_COLOR) -> ft.Border:
    side = ft.BorderSide(1, color)
    return ft.Border(side, side, side, side)
