import flet as ft


def model_card(
    name: str,
    country: str,
    country_code: str,
    description: str,
    input_size: int,
    horizon: int,
    frequency: str,
    max_steps: int,
    on_click: ft.EventHandler,
) -> ft.Card:
    return ft.Card(
        elevation=0,
        bgcolor=ft.Colors.WHITE,
        content=_card_container(
            controls=[
                _model_header(name, country),
                _description(description),
                _model_tags(country_code, input_size, horizon, frequency, max_steps),
                _use_model_button(on_click),
            ],
        ),
    )


def _card_container(controls: list[ft.Control]) -> ft.Container:
    return ft.Container(
        padding=20,
        border=_border("#E2E8F0"),
        border_radius=14,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.START,
            controls=controls,
            spacing=14,
        ),
    )


def _model_header(name: str, country: str) -> ft.Row:
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            ft.Column(
                spacing=2,
                expand=True,
                controls=[
                    ft.Text(
                        name,
                        size=19,
                        weight=ft.FontWeight.W_600,
                        color="#0F172A",
                    ),
                    _country_label(country),
                ],
            ),
            ft.Icon(ft.Icons.INSIGHTS_OUTLINED, size=22, color="#64748B"),
        ],
    )


def _country_label(country: str) -> ft.Row:
    return ft.Row(
        spacing=6,
        controls=[
            ft.Icon(ft.Icons.PUBLIC, size=15, color="#64748B"),
            ft.Text(country, size=13, color="#64748B"),
        ],
    )


def _description(description: str) -> ft.Text:
    return ft.Text(description, size=13, color="#475569")


def _model_tags(
    country_code: str,
    input_size: int,
    horizon: int,
    frequency: str,
    max_steps: int,
) -> ft.Row:
    return ft.Row(
        wrap=True,
        spacing=8,
        run_spacing=8,
        controls=[
            _tag(country_code),
            _tag(f"{input_size} h input"),
            _tag(f"{horizon} h horizonte"),
            _tag(frequency),
            _tag(f"{max_steps} steps"),
        ],
    )


def _use_model_button(on_click: ft.EventHandler) -> ft.TextButton:
    return ft.TextButton(
        "Usar modelo",
        icon=ft.Icons.ARROW_FORWARD,
        icon_color="#0F172A",
        style=ft.ButtonStyle(color="#0F172A"),
        on_click=on_click,
    )


def _tag(label: str) -> ft.Container:
    return ft.Container(
        padding=ft.Padding(10, 5, 10, 5),
        border=_border("#CBD5E1"),
        border_radius=999,
        content=ft.Text(label, size=12, color="#334155"),
    )


def _border(color: str) -> ft.Border:
    side = ft.BorderSide(1, color)
    return ft.Border(side, side, side, side)
