from __future__ import annotations

import flet as ft

OperationState = tuple[str, str, str]


class BackgroundOperations:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.title = ft.Text("Operacion en segundo plano", size=13, weight=ft.FontWeight.W_600, color="#0F172A")
        self.message = ft.Text("", size=12, color="#475569")
        self.progress = ft.ProgressRing(width=28, height=28, stroke_width=3, color="#0F172A")
        self.status_icon = ft.Text("", size=24, visible=False)
        self.card = ft.Container(
            right=18,
            bottom=18,
            width=340,
            padding=ft.Padding(14, 12, 14, 12),
            bgcolor="#FFFFFF",
            border=ft.Border(
                ft.BorderSide(1, "#E2E8F0"),
                ft.BorderSide(1, "#E2E8F0"),
                ft.BorderSide(1, "#E2E8F0"),
                ft.BorderSide(1, "#E2E8F0"),
            ),
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=18,
                spread_radius=1,
                color="#33415526",
                offset=ft.Offset(0, 6),
            ),
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self.progress,
                    self.status_icon,
                    ft.Column(spacing=2, expand=True, controls=[self.title, self.message]),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=16,
                        tooltip="Ocultar",
                        on_click=lambda _: self.clear_finished(),
                    ),
                ],
            ),
            visible=False,
        )
        self.operations: dict[str, OperationState] = {}
        self.page.overlay.append(self.card)

    def show(self, title: str, message: str, key: str = "default") -> None:
        self.operations[key] = (title, message, "running")
        self._render()

    def finish(
        self,
        title: str,
        message: str,
        *,
        success: bool,
        key: str = "default",
    ) -> None:
        self.operations[key] = (title, message, "success" if success else "error")
        self._render()

    def hide(self, key: str = "default") -> None:
        self.operations.pop(key, None)
        self._render()

    def clear_finished(self) -> None:
        self.operations = {
            key: operation
            for key, operation in self.operations.items()
            if operation[2] == "running"
        }
        self._render()

    def _render(self) -> None:
        if not self.operations:
            self.card.visible = False
            self.page.update()
            return
        title, message, state = next(reversed(self.operations.values()))
        self.title.value = title
        self.message.value = message
        self.progress.visible = state == "running"
        self.status_icon.visible = state != "running"
        self.status_icon.value = "OK" if state == "success" else "!"
        self.status_icon.color = "#047857" if state == "success" else "#B91C1C"
        self.card.visible = True
        self.page.update()
