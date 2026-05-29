from __future__ import annotations

import flet as ft

OperationState = tuple[str, str, str]


class BackgroundOperations:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.minimized = False
        self.title = ft.Text("Operacion en segundo plano", size=13, weight=ft.FontWeight.W_600, color="#0F172A")
        self.message = ft.Text("", size=12, color="#475569")
        self.progress = ft.ProgressRing(width=28, height=28, stroke_width=3, color="#0F172A")
        self.status_icon = ft.Text("", size=24, visible=False)
        self.action_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color=ft.Colors.WHITE,
            icon_size=12,
            width=22,
            height=22,
            padding=0,
            tooltip="Ocultar",
            bgcolor="#DC2626",
            opacity=0,
            on_click=self._handle_action,
        )
        self.content_row = ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.progress,
                self.status_icon,
                ft.Column(spacing=2, expand=True, controls=[self.title, self.message]),
            ],
        )
        self.card = ft.Container(
            width=250,
            padding=ft.Padding(14, 12, 14, 12),
            alignment=ft.Alignment(0, 0),
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
            content=self.content_row,
            on_click=self._restore,
        )
        self.stack = ft.Stack(
            controls=[
                self.card,
                ft.Container(
                    content=self.action_button,
                    right=-8,
                    top=-8,
                ),
            ],
            width=250,
            clip_behavior=ft.ClipBehavior.NONE,
        )
        self.hover_area = ft.Container(
            content=self.stack,
            padding=ft.Padding(0, 8, 8, 0),
            on_hover=self._toggle_action_button,
        )
        self.wrapper = ft.Container(
            left=0,
            right=0,
            bottom=20,
            alignment=ft.Alignment(0, 1),
            content=self.hover_area,
            visible=False,
        )
        self.operations: dict[str, OperationState] = {}
        self.page.overlay.append(self.wrapper)

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
        if not self.operations:
            self.minimized = False
        self._render()

    def _handle_action(self, _: ft.ControlEvent) -> None:
        if self._has_running_operation():
            self.minimized = True
            self._render()
            return
        self.clear_finished()

    def _restore(self, _: ft.ControlEvent) -> None:
        if not self.minimized:
            return
        self.minimized = False
        self._render()

    def _toggle_action_button(self, event: ft.ControlEvent) -> None:
        self.action_button.opacity = 1 if event.data else 0
        self.page.update()

    def _has_running_operation(self) -> bool:
        return any(operation[2] == "running" for operation in self.operations.values())

    def _render(self) -> None:
        if not self.operations:
            self.wrapper.visible = False
            self.page.update()
            return
        title, message, state = next(reversed(self.operations.values()))
        self.title.value = title
        self.message.value = message
        self.progress.visible = state == "running"
        self.status_icon.visible = state != "running"
        self.status_icon.value = "OK" if state == "success" else "!"
        self.status_icon.color = "#047857" if state == "success" else "#B91C1C"
        self.action_button.icon = ft.Icons.MINIMIZE if self._has_running_operation() else ft.Icons.CLOSE
        self.action_button.bgcolor = "#334155" if self._has_running_operation() else "#DC2626"
        self.action_button.tooltip = "Minimizar" if self._has_running_operation() else "Ocultar"
        self.content_row.controls[2].visible = not self.minimized
        self.content_row.alignment = ft.MainAxisAlignment.CENTER if self.minimized else ft.MainAxisAlignment.START
        self.content_row.spacing = 0 if self.minimized else 12
        self.card.width = 56 if self.minimized else 250
        self.card.height = 56 if self.minimized else None
        self.card.padding = ft.Padding(14, 14, 14, 14) if self.minimized else ft.Padding(14, 12, 14, 12)
        self.stack.width = 56 if self.minimized else 250
        self.stack.height = 56 if self.minimized else None
        self.hover_area.width = 64 if self.minimized else 258
        self.hover_area.height = 64 if self.minimized else None
        self.wrapper.visible = True
        self.page.update()
