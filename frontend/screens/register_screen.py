import flet as ft
from api_client import api
from components.dialogs import show_error_dialog, show_success_dialog


class RegisterScreen:
    def __init__(self, page: ft.Page):
        self.page = page
        self.username = ft.TextField(label="Логин *", prefix_icon=ft.Icons.PERSON)
        self.email = ft.TextField(label="Email *", prefix_icon=ft.Icons.EMAIL)
        self.full_name = ft.TextField(label="ФИО *", prefix_icon=ft.Icons.PERSON)
        self.password = ft.TextField(label="Пароль * (мин. 6 символов)", prefix_icon=ft.Icons.LOCK, password=True, can_reveal_password=True)
        self.role = ft.Dropdown(
            label="Роль",
            value="manager",
            options=[
                ft.dropdown.Option("admin", "Администратор"),
                ft.dropdown.Option("manager", "Мастер-приёмщик"),
                ft.dropdown.Option("accountant", "Бухгалтер"),
            ],
        )
        self.loading = ft.ProgressRing(visible=False, width=20, height=20)

    def build(self):
        return ft.Container(
            width=450,
            padding=40,
            border_radius=12,
            bgcolor=ft.Colors.GREY_800,
            content=ft.Column(
                [
                    ft.Text("Регистрация", size=24, weight=ft.FontWeight.BOLD),
                    self.username,
                    self.email,
                    self.full_name,
                    self.password,
                    self.role,
                    ft.Row(
                        [self.loading, ft.ElevatedButton("Создать аккаунт", on_click=lambda e: self._register())],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.TextButton("Уже есть аккаунт? Войти", on_click=lambda e: None),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                spacing=12,
            ),
        )

    async def _register(self):
        if not all([self.username.value, self.email.value, self.full_name.value, self.password.value]):
            show_error_dialog(self.page, "Ошибка", "Заполните все обязательные поля")
            return
        if len(self.password.value) < 6:
            show_error_dialog(self.page, "Ошибка", "Пароль должен быть не короче 6 символов")
            return
        self.loading.visible = True
        self.page.update()
        try:
            await api.register({
                "username": self.username.value.strip(),
                "email": self.email.value.strip(),
                "full_name": self.full_name.value.strip(),
                "password": self.password.value,
                "role": self.role.value,
            })
            show_success_dialog(self.page, "Пользователь создан! Теперь войдите.", lambda: None)
        except Exception as e:
            show_error_dialog(self.page, "Ошибка регистрации", str(e))
        finally:
            self.loading.visible = False
            self.page.update()