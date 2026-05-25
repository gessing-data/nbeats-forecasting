import flet as ft


def build_forecast_workspace_page(model: dict[str, object]) -> ft.Control:
    return _page_shell(_workspace_content(model))


def _page_shell(content: ft.Control) -> ft.Container:
    return ft.Container(
        expand=True,
        bgcolor="#F8FAFC",
        alignment=ft.Alignment(0, -1),
        content=ft.Container(
            width=968,
            padding=ft.Padding(24, 28, 24, 28),
            content=content,
        ),
    )


def _workspace_content(model: dict[str, object]) -> ft.Column:
    return ft.Column(
        spacing=18,
        controls=[
            _page_title(),
            _selected_model_panel(model),
            _model_info_grid(model),
        ],
    )


def _page_title() -> ft.Text:
    return ft.Text(
        "Workspace de forecast",
        size=28,
        weight=ft.FontWeight.W_600,
        color="#0F172A",
    )


def _selected_model_panel(model: dict[str, object]) -> ft.Container:
    return ft.Container(
        padding=22,
        bgcolor="#FFFFFF",
        border=_border("#E2E8F0"),
        border_radius=16,
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Text("Modelo seleccionado", size=13, color="#64748B"),
                ft.Text(
                    str(model["name"]),
                    size=22,
                    weight=ft.FontWeight.W_600,
                    color="#0F172A",
                ),
                ft.Text(
                    "Esta pagina sera usada para configurar la entrada, ejecutar el forecast y visualizar resultados.",
                    size=14,
                    color="#475569",
                ),
            ],
        ),
    )


def _model_info_grid(model: dict[str, object]) -> ft.ResponsiveRow:
    return ft.ResponsiveRow(
        spacing=12,
        run_spacing=12,
        controls=[
            _info_item(ft.Icons.PUBLIC, "Zona", str(model["zone"])),
            _info_item(ft.Icons.TIMELINE, "Input size", f"{model['input_size']} horas"),
            _info_item(
                ft.Icons.QUERY_STATS,
                "Horizonte",
                f"{model['horizon']} horas",
            ),
            _info_item(ft.Icons.SCHEDULE, "Frecuencia", str(model["frequency"])),
            _info_item(ft.Icons.SETTINGS, "Max steps", str(model["max_steps"])),
        ],
    )


def _info_item(icon: str, label: str, value: str) -> ft.Container:
    return ft.Container(
        padding=16,
        bgcolor="#FFFFFF",
        border=_border("#E2E8F0"),
        border_radius=14,
        col={"xs": 12, "sm": 6, "md": 3},
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Icon(icon, size=20, color="#64748B"),
                ft.Text(label, size=12, color="#64748B"),
                ft.Text(value, size=15, weight=ft.FontWeight.W_600, color="#0F172A"),
            ],
        ),
    )


def _border(color: str) -> ft.Border:
    side = ft.BorderSide(1, color)
    return ft.Border(side, side, side, side)
