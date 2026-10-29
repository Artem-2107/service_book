import flet as ft
from api_client import api
from components.dialogs import show_error_dialog, show_confirm_dialog


class CarsScreen:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page_num = 1
        self.page_size = 15
        self.search_query = ""
        self.data = {"items": [], "total": 0, "pages": 0}
        self.search_field = ft.TextField(hint_text="Поиск по госномеру...", prefix_icon=ft.Icons.SEARCH, width=300, on_submit=lambda e: self._search())
        self.list_view = ft.Column(spacing=8, expand=True)
        self.page_info = ft.Text("", size=12, color=ft.Colors.GREY)
        self.loading = ft.ProgressRing(visible=False, width=20, height=20)

    def build(self) -> ft.Control:
        self.page.run_task(self._load)
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Автомобили", size=24, weight=ft.FontWeight.BOLD, expand=True),
                        self.search_field,
                        ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda e: self._load()),
                        ft.ElevatedButton("Добавить авто", icon=ft.Icons.ADD, on_click=lambda e: self._open_form()),
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
            self.data = await api.list_cars(page=self.page_num, page_size=self.page_size, search=self.search_query or None)
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
                    ft.Text("Клиент ID", width=90, weight=ft.FontWeight.BOLD),
                    ft.Text("Марка/Модель", width=200, weight=ft.FontWeight.BOLD),
                    ft.Text("Госномер", width=120, weight=ft.FontWeight.BOLD),
                    ft.Text("VIN", width=170, weight=ft.FontWeight.BOLD),
                    ft.Text("Год", width=60, weight=ft.FontWeight.BOLD),
                    ft.Text("Действия", width=150, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            )
        )
        self.list_view.controls.append(ft.Divider())
        if not self.data["items"]:
            self.list_view.controls.append(ft.Container(content=ft.Text("Автомобили не найдены", color=ft.Colors.GREY), padding=40, alignment=ft.alignment.center))
            return
        for c in self.data["items"]:
            row = ft.Row(
                [
                    ft.Text(str(c["id"]), width=60),
                    ft.Text(str(c["client_id"]), width=90),
                    ft.Text(f"{c['brand']} {c['model']}", width=200, weight=ft.FontWeight.W_500),
                    ft.Container(content=ft.Text(c["plate"], weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.YELLOW_100, color=ft.Colors.BLACK, padding=ft.padding.symmetric(4, 8), border_radius=4, width=120),
                    ft.Text(c.get("vin") or "—", width=170, size=12),
                    ft.Text(str(c.get("year") or "—"), width=60),
                    ft.Row(
                        [
                            ft.IconButton(icon=ft.Icons.EDIT, on_click=lambda e, cid=c["id"]: self._open_form(cid)),
                            ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400, on_click=lambda e, cid=c["id"], p=c["plate"]: self._delete(cid, p)),
                        ],
                        width=150,
                    ),
                ],
                spacing=8,
            )
            self.list_view.controls.append(row)

    async def _delete(self, car_id: int, plate: str):
        def do_delete():
            self.page.run_task(self._do_delete, car_id)
        show_confirm_dialog(self.page, "Удаление авто", f"Удалить авто {plate}? Все заказы этого авто будут удалены!", do_delete)

    async def _do_delete(self, car_id: int):
        try:
            await api.delete_car(car_id)
            await self._load()
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))

    def _open_form(self, car_id: int = None):
        dlg = CarFormDialog(self.page, car_id, on_saved=lambda: self._load())
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()


class CarFormDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page, car_id: int = None, on_saved=None):
        super().__init__(modal=True)
        self.page = page
        self.car_id = car_id
        self.on_saved = on_saved
        self.client_id = ft.TextField(label="ID клиента *", keyboard_type=ft.KeyboardType.NUMBER)
        self.brand = ft.TextField(label="Марка *")
        self.model = ft.TextField(label="Модель *")
        self.plate = ft.TextField(label="Госномер *")
        self.vin = ft.TextField(label="VIN (17 символов)", max_length=17)
        self.year = ft.TextField(label="Год выпуска", keyboard_type=ft.KeyboardType.NUMBER)
        self.notes = ft.TextField(label="Заметки", multiline=True, min_lines=2)
        self.title = ft.Text("Новый автомобиль" if not car_id else "Редактирование")
        self.content = ft.Column([self.client_id, self.brand, self.model, self.plate, self.vin, self.year, self.notes], tight=True, scroll=ft.ScrollMode.AUTO)
        self.actions = [
            ft.TextButton("Отмена", on_click=lambda e: self._close()),
            ft.ElevatedButton("Сохранить", on_click=lambda e: self._save()),
        ]
        if car_id:
            self.page.run_task(self._load_data)

    async def _load_data(self):
        try:
            data = await api.list_cars(page=1, page_size=1000)
            for c in data["items"]:
                if c["id"] == self.car_id:
                    self.client_id.value = str(c["client_id"])
                    self.brand.value = c["brand"]
                    self.model.value = c["model"]
                    self.plate.value = c["plate"]
                    self.vin.value = c.get("vin") or ""
                    self.year.value = str(c.get("year") or "")
                    self.notes.value = c.get("notes") or ""
                    self.page.update()
                    break
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))

    def _close(self):
        self.open = False
        self.page.update()

    async def _save(self):
        try:
            client_id = int(self.client_id.value)
        except ValueError:
            show_error_dialog(self.page, "Ошибка", "ID клиента должен быть числом")
            return
        if not all([self.brand.value, self.model.value, self.plate.value]):
            show_error_dialog(self.page, "Ошибка", "Заполните обязательные поля")
            return
        payload = {
            "client_id": client_id,
            "brand": self.brand.value.strip(),
            "model": self.model.value.strip(),
            "plate": self.plate.value.strip(),
            "vin": self.vin.value.strip() or None,
            "year": int(self.year.value) if self.year.value.strip() else None,
            "notes": self.notes.value.strip() or None,
        }
        try:
            if self.car_id:
                await api.update_car(self.car_id, payload)
            else:
                await api.create_car(payload)
            self._close()
            if self.on_saved:
                self.on_saved()
        except Exception as e:
            show_error_dialog(self.page, "Ошибка сохранения", str(e))
