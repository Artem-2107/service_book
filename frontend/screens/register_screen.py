import flet as ft
from api_client import api
from components.dialogs import show_error_dialog, show_success_dialog


class RegisterScreen:
    def __init__(self, page: ft.Page, on_go_login=None):
        self.page = page
        self.on_go_login = on_go_login
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
                        [self.loading, ft.ElevatedButton("Создать аккаунт", on_click=self._on_register_click)],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.TextButton("Уже есть аккаунт? Войти", on_click=self._go_login),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                spacing=12,
            ),
        )

    def _go_login(self, e=None):
        if self.on_go_login:
            self.on_go_login()

    # ГЛАВНОЕ ИСПРАВЛЕНИЕ: раньше на кнопку вешался async-обработчик напрямую
    # (lambda e: self._register()). Flet НЕ запускает async-функции из on_click —
    # создавалась корутина, которая никогда не выполнялась, и кнопка молчала.
    # Теперь синхронный обработчик запускает задачу через page.run_task
    # (так же, как на экране входа).
    def _on_register_click(self, e):
        self.page.run_task(self._register)

    async def _register(self):
        # ИСПРАВЛЕНИЕ: защита от None — при пустых полях падало на .strip()/len(None)
        username = (self.username.value or "").strip()
        email = (self.email.value or "").strip()
        full_name = (self.full_name.value or "").strip()
        password = self.password.value or ""
        role = self.role.value or "manager"

        if not all([username, email, full_name, password]):
            show_error_dialog(self.page, "Ошибка", "Заполните все обязательные поля")
            return
        if len(password) < 6:
            show_error_dialog(self.page, "Ошибка", "Пароль должен быть не короче 6 символов")
            return
        if "@" not in email:
            show_error_dialog(self.page, "Ошибка", "Введите корректный email")
            return

        self.loading.visible = True
        self.page.update()
        try:
            await api.register({
                "username": username,
                "email": email,
                "full_name": full_name,
                "password": password,
                "role": role,
            })
            show_success_dialog(self.page, "Пользователь создан! Теперь войдите.", self._go_login)
        except Exception as e:
            show_error_dialog(self.page, "Ошибка регистрации", str(e))
        finally:
            self.loading.visible = False
            self.page.update()