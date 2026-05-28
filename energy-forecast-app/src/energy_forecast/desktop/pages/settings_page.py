import os
import platform
import subprocess

import flet as ft

from energy_forecast.app_paths import AppPaths, load_settings


def build_settings_page(page: ft.Page, paths: AppPaths) -> ft.Control:
    settings = load_settings(paths)
    seeds = settings.get("seeds", {})
    initialized = bool(seeds.get("initialized")) if isinstance(seeds, dict) else False

    return _page_shell(
        ft.Column(
            spacing=18,
            controls=[
                _page_title("Configuracion de la app"),
                _workspace_section(page, paths),
                _datasets_section(initialized),
            ],
        )
    )


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


def _page_title(title: str) -> ft.Text:
    return ft.Text(
        title,
        size=28,
        weight=ft.FontWeight.W_600,
        color="#0F172A",
    )


def _workspace_section(page: ft.Page, paths: AppPaths) -> ft.Container:
    return _settings_card(
        ft.Column(
            spacing=14,
            controls=[
                _section_header(
                    "Workspace",
                    "La app guarda datos de trabajo en data/ y modelos con sus runs en models/.",
                ),
                ft.TextField(
                    label="Ruta actual",
                    value=str(paths.workspace_root),
                    read_only=True,
                    border_color="#CBD5E1",
                    focused_border_color="#334155",
                ),
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            "Abrir carpeta",
                            icon=ft.Icons.FOLDER_OPEN,
                            on_click=lambda _: _open_workspace_folder(page, paths),
                        )
                    ]
                ),
            ],
        )
    )


def _datasets_section(initialized: bool) -> ft.Container:
    status_text = "Preparados" if initialized else "Pendientes"
    status_color = "#047857" if initialized else "#B45309"

    return _settings_card(
        ft.Column(
            spacing=14,
            controls=[
                _section_header(
                    "Datasets base",
                    "Los seeders OPSD se agregaran despues. Por ahora no se descarga ni procesa nada automaticamente.",
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Text("Estado:", size=14, color="#475569"),
                        ft.Text(status_text, size=14, color=status_color, weight=ft.FontWeight.W_600),
                    ],
                ),
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.FilledButton("Preparar datasets base", disabled=True),
                        ft.OutlinedButton("Reiniciar datasets base", disabled=True),
                    ],
                ),
            ],
        )
    )


def _settings_card(content: ft.Control) -> ft.Container:
    border_side = ft.BorderSide(1, "#E2E8F0")

    return ft.Container(
        padding=ft.Padding(18, 18, 18, 18),
        bgcolor="#FFFFFF",
        border=ft.Border(border_side, border_side, border_side, border_side),
        border_radius=16,
        content=content,
    )


def _section_header(title: str, description: str) -> ft.Column:
    return ft.Column(
        spacing=4,
        controls=[
            ft.Text(title, size=18, weight=ft.FontWeight.W_600, color="#0F172A"),
            ft.Text(description, size=13, color="#64748B"),
        ],
    )


def _open_workspace_folder(page: ft.Page, paths: AppPaths) -> None:
    try:
        if platform.system() == "Windows":
            os.startfile(paths.workspace_root)  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(paths.workspace_root)])
        else:
            subprocess.Popen(["xdg-open", str(paths.workspace_root)])
    except OSError as error:
        page.snack_bar = ft.SnackBar(
            ft.Text(f"No se pudo abrir la carpeta: {error}"),
            bgcolor="#991B1B",
        )
        page.snack_bar.open = True
        page.update()
