import flet as ft
from api_client import api
from components.dialogs import show_error_dialog, show_confirm_dialog


class ClientsScreen:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page_num = 1
        self.page_size = 15
        self.search_query = ""
        self.data = {"items": [], "total": 0, "pages": 0}
        self.search_field = ft.TextField(hint_text="Поиск по ФИО...", prefix_icon=ft.Icons.SEARCH, width=300, on_submit=lambda e: self._search(), border_radius=8)
        self.list_view = ft.Column(spacing=8, expand=True)
        self.page_info = ft.Text("", size=12, color=ft.Colors.GREY)
        self.loading = ft.ProgressRing(visible=False, width=20, height=20)

    def build(self) -> ft.Control:
        self.page.run_task(self._load)
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Клиенты", size=24, weight=ft.FontWeight.BOLD, expand=True),
                        self.search_field,
                        ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Обновить", on_click=lambda e: self._load()),
                        ft.ElevatedButton("Добавить клиента", icon=ft.Icons.PERSON_ADD, on_click=lambda e: self._open_form()),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row([self.loading, self.page_info], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                self.list_view,
                self._build_pagination(),
            ],
            expand=True,
        )

    def _build_pagination(self) -> ft.Control:
        return ft.Row(
            [
                ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, on_click=lambda e: self._goto(self.page_num - 1), disabled=self.page_num <= 1),
                ft.Text(f"Стр. {self.page_num} из {self.data.get('pages', 1)}", size=13),
                ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, on_click=lambda e: self._goto(self.page_num + 1), disabled=self.page_num >= self.data.get("pages", 1)),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

    async def _goto(self, page: int):
        self.page_num = max(1, page)
        await self._load()

    async def _search(self):
        self.search_query = self.search_field.value.strip()
        self.page_num = 1
        await self._load()

    async def _load(self):
        self.loading.visible = True
        self.page.update()
        try:
            self.data = await api.list_clients(page=self.page_num, page_size=self.page_size, search=self.search_query or None)
            self._render_list()
            self.page_info.value = f"Всего записей: {self.data['total']}"
        except Exception as e:
            show_error_dialog(self.page, "Ошибка загрузки", str(e))
        finally:
            self.loading.visible = False
            self.page.update()

    def _render_list(self):
        self.list_view.controls.clear()
        self.list_view.controls.append(
            ft.Row(
                [
                    ft.Text("ID", width=60, weight=ft.FontWeight.BOLD),
                    ft.Text("ФИО", width=250, weight=ft.FontWeight.BOLD),
                    ft.Text("Телефон", width=150, weight=ft.FontWeight.BOLD),
                    ft.Text("Email", width=200, weight=ft.FontWeight.BOLD),
                    ft.Text("Действия", width=150, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            )
        )
        self.list_view.controls.append(ft.Divider())
        if not self.data["items"]:
            self.list_view.controls.append(ft.Container(content=ft.Text("Клиенты не найдены", color=ft.Colors.GREY), padding=40, alignment=ft.alignment.center))
            return
        for c in self.data["items"]:
            row = ft.Row(
                [
                    ft.Text(str(c["id"]), width=60),
                    ft.Text(c["fio"], width=250, weight=ft.FontWeight.W_500),
                    ft.Text(c.get("phone") or "—", width=150),
                    ft.Text(c.get("email") or "—", width=200),
                    ft.Row(
                        [
                            ft.IconButton(icon=ft.Icons.EDIT, tooltip="Редактировать", on_click=lambda e, cid=c["id"]: self._open_form(cid)),
                            ft.IconButton(icon=ft.Icons.DELETE, tooltip="Удалить", icon_color=ft.Colors.RED_400, on_click=lambda e, cid=c["id"], fio=c["fio"]: self._delete(cid, fio)),
                        ],
                        width=150,
                    ),
                ],
                spacing=8,
            )
            self.list_view.controls.append(row)

    async def _delete(self, client_id: int, fio: str):
        def do_delete():
            self.page.run_task(self._do_delete, client_id)
        show_confirm_dialog(self.page, "Удаление клиента", f"Удалить клиента \'{fio}\'? Все его авто и заказы будут удалены!", do_delete)

    async def _do_delete(self, client_id: int):
        try:
            await api.delete_client(client_id)
            await self._load()
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))

    def _open_form(self, client_id: int = None):
        dlg = ClientFormDialog(self.page, client_id, on_saved=lambda: self._load())
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()


class ClientFormDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page, client_id: int = None, on_saved=None):
        super().__init__(modal=True)
        self.page = page
        self.client_id = client_id
        self.on_saved = on_saved
        self.fio = ft.TextField(label="ФИО *", autofocus=True)
        self.phone = ft.TextField(label="Телефон")
        self.email = ft.TextField(label="Email")
        self.notes = ft.TextField(label="Заметки", multiline=True, min_lines=2, max_lines=4)
        self.title = ft.Text("Новый клиент" if not client_id else "Редактирование клиента")
        self.content = ft.Column([self.fio, self.phone, self.email, self.notes], tight=True)
        self.actions = [
            ft.TextButton("Отмена", on_click=lambda e: self._close()),
            ft.ElevatedButton("Сохранить", on_click=lambda e: self._save()),
        ]
        if client_id:
            self.page.run_task(self._load_data)

    async def _load_data(self):
        try:
            data = await api.list_clients(page=1, page_size=1000)
            for c in data["items"]:
                if c["id"] == self.client_id:
                    self.fio.value = c["fio"]
                    self.phone.value = c.get("phone") or ""
                    self.email.value = c.get("email") or ""
                    self.notes.value = c.get("notes") or ""
                    self.page.update()
                    break
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))

    def _close(self):
        self.open = False
        self.page.update()

    async def _save(self):
        if not self.fio.value.strip():
            show_error_dialog(self.page, "Ошибка", "ФИО обязательно")
            return
        payload = {
            "fio": self.fio.value.strip(),
            "phone": self.phone.value.strip() or None,
            "email": self.email.value.strip() or None,
            "notes": self.notes.value.strip() or None,
        }
        try:
            if self.client_id:
                await api.update_client(self.client_id, payload)
            else:
                await api.create_client(payload)
            self._close()
            if self.on_saved:
                self.on_saved()
        except Exception as e:
            show_error_dialog(self.page, "Ошибка сохранения", str(e))
