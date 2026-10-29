import flet as ft
from api_client import api


class LoginScreen:
    def __init__(self, page: ft.Page, on_success, on_register_click):
        self.page = page
        self.on_success = on_success
        self.on_register_click = on_register_click
        self.username = ft.TextField(label="Логин", prefix_icon=ft.Icons.PERSON, autofocus=True)
        self.password = ft.TextField(label="Пароль", prefix_icon=ft.Icons.LOCK, password=True, can_reveal_password=True)
        self.error_text = ft.Text("", color=ft.Colors.RED_400, size=12)
        self.loading = ft.ProgressRing(visible=False, width=20, height=20)

    def build(self):
        return ft.Container(
            width=400, padding=40, border_radius=12, bgcolor=ft.Colors.GREY_800,
            content=ft.Column([
                ft.Icon(ft.Icons.BUILD, size=64, color=ft.Colors.BLUE),
                ft.Text("ServiceBook", size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text("Система учёта автосервиса", size=14, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
                ft.Divider(height=24, color=ft.Colors.TRANSPARENT),
                self.username, self.password, self.error_text,
                ft.ElevatedButton("Войти", width=200, on_click=self._login),
                self.loading,
                ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                ft.TextButton("Нет аккаунта? Зарегистрироваться", on_click=self.on_register_click),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
        )

    def _login(self, e):
        self.error_text.value = ""
        self.loading.visible = True
        self.page.update()

        async def do_login():
            try:
                data = await api.login(self.username.value.strip(), self.password.value)
                user_data = data.get("user", {})
                self.on_success(user_data)
            except Exception as ex:
                self.error_text.value = str(ex)
            finally:
                self.loading.visible = False
                self.page.update()

        self.page.run_task(do_login)