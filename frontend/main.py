import flet as ft
from config import APP_TITLE
from api_client import api
from screens.main_screen import MainScreen
from screens.login_screen import LoginScreen
from screens.register_screen import RegisterScreen


def main(page: ft.Page):
    page.title = APP_TITLE
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = ft.Colors.GREY_900

    # Автоматическое определение: телефон или ПК
    is_mobile = page.platform in ["android", "ios"]

    if is_mobile:
        try:
            page.window.width = 390
            page.window.height = 844
            page.window.resizable = False
        except Exception:
            pass
    else:
        page.window.width = 1280
        page.window.height = 800
        page.window.resizable = True

    page.user_data = None

    def show_login():
        page.clean()
        page.appbar = None

        def on_success(user_data):
            page.user_data = user_data
            show_main()

        def on_register_click():
            show_register()

        login = LoginScreen(page, on_success, on_register_click)
        page.add(ft.Container(content=login.build(), expand=True, alignment=ft.alignment.center))
        page.update()

    def show_register():
        page.clean()
        page.appbar = None
        reg = RegisterScreen(page)
        page.add(ft.Container(content=reg.build(), expand=True, alignment=ft.alignment.center))
        page.update()

    def show_main():
        page.clean()

        def on_logout():
            api.clear_token()
            page.user_data = None
            show_login()

        main_scr = MainScreen(page, page.user_data, on_logout)
        page.appbar = main_scr.get_app_bar()
        page.add(main_scr.build())
        page.update()

    show_login()


if __name__ == "__main__":
    ft.app(target=main)