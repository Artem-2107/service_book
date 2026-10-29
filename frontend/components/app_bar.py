import flet as ft


def build_app_bar(page: ft.Page, on_logout) -> ft.AppBar:
    user_info = page.session.get("user") or {}
    return ft.AppBar(
        leading=ft.Icon(ft.Icons.BUILDR, color=ft.Colors.WHITE),
        leading_width=40,
        title=ft.Text("ServiceBook", size=18, weight=ft.FontWeight.BOLD),
        bgcolor=ft.Colors.BLUE_GREY_900,
        actions=[
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=18),
                        ft.Column(
                            [
                                ft.Text(user_info.get("full_name", "—"), size=12, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
                                ft.Text(user_info.get("role", "").upper(), size=10, color=ft.Colors.WHITE70),
                            ],
                            spacing=0,
                        ),
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.END,
                ),
                padding=ft.padding.only(right=16),
            ),
            ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Выйти", on_click=lambda e: on_logout()),
        ],
    )
