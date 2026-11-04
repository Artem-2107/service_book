import flet as ft
from typing import Callable, Optional


def close_dialog(page: ft.Page):
    if page.dialog:
        page.dialog.open = False
        page.dialog = None
        page.update()


def show_error_dialog(page: ft.Page, title: str, message: str):
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(title, color=ft.Colors.RED_400),
        content=ft.Text(message),
        actions=[ft.TextButton("OK", on_click=lambda e: close_dialog(page))],
    )
    page.dialog = dlg
    dlg.open = True
    page.update()


def show_error_with_retry(page: ft.Page, title: str, message: str, on_retry: Callable):
    """Диалог ошибки с кнопкой 'Повторить' — для сетевых ошибок."""
    def on_retry_click(e):
        close_dialog(page)
        on_retry()
        
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(title, color=ft.Colors.RED_400),
        content=ft.Text(message),
        actions=[
            ft.TextButton("Отмена", on_click=lambda e: close_dialog(page)),
            ft.TextButton("Повторить", on_click=on_retry_click, color=ft.Colors.BLUE),
        ],
    )
    page.dialog = dlg
    dlg.open = True
    page.update()


def show_success_dialog(page: ft.Page, message: str, on_ok: Optional[Callable] = None):
    def on_ok_click(e):
        close_dialog(page)
        if on_ok:
            on_ok()
            
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("✅ Успешно", color=ft.Colors.GREEN_400),
        content=ft.Text(message),
        actions=[ft.TextButton("OK", on_click=on_ok_click)],
    )
    page.dialog = dlg
    dlg.open = True
    page.update()


def show_confirm_dialog(page: ft.Page, title: str, message: str, on_confirm: Callable):
    def on_confirm_click(e):
        close_dialog(page)
        on_confirm()
        
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(message),
        actions=[
            ft.TextButton("Отмена", on_click=lambda e: close_dialog(page)),
            ft.TextButton(
                "Подтвердить", 
                on_click=on_confirm_click, 
                style=ft.ButtonStyle(color=ft.Colors.RED_400)
            ),
        ],
    )
    page.dialog = dlg
    dlg.open = True
    page.update()