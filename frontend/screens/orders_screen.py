import flet as ft
from api_client import api
from components.dialogs import show_error_dialog, show_confirm_dialog


STATUS_LABELS = {
    "new": ("🆕 Новый", ft.Colors.BLUE),
    "in_progress": ("🔧 В работе", ft.Colors.ORANGE),
    "waiting": ("⏳ Ожидает запчастей", ft.Colors.AMBER),
    "done": ("✅ Готов", ft.Colors.GREEN),
    "issued": ("📦 Выдан", ft.Colors.TEAL),
    "cancelled": ("❌ Отменён", ft.Colors.RED),
}


class OrdersScreen:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page_num = 1
        self.page_size = 15
        self.status_filter = None
        self.data = {"items": [], "total": 0, "pages": 0}
        self.status_dd = ft.Dropdown(
            label="Фильтр по статусу", width=250,
            options=[ft.dropdown.Option(key="", text="— Все —")] + [ft.dropdown.Option(k, v[0]) for k, v in STATUS_LABELS.items()],
            value="", on_change=lambda e: self._filter(),
        )
        self.list_view = ft.Column(spacing=8, expand=True)
        self.page_info = ft.Text("", size=12, color=ft.Colors.GREY)
        self.loading = ft.ProgressRing(visible=False, width=20, height=20)

    def build(self) -> ft.Control:
        self.page.run_task(self._load)
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Заказы-наряды", size=24, weight=ft.FontWeight.BOLD, expand=True),
                        self.status_dd,
                        ft.IconButton(icon=ft.Icons.REFRESH, on_click=lambda e: self._load()),
                        ft.ElevatedButton("Новый заказ", icon=ft.Icons.ADD, on_click=lambda e: self._open_form()),
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

    async def _filter(self):
        self.status_filter = self.status_dd.value or None
        self.page_num = 1
        await self._load()

    async def _load(self):
        self.loading.visible = True
        self.page.update()
        try:
            self.data = await api.list_orders(page=self.page_num, page_size=self.page_size, status=self.status_filter)
            self._render_list()
            self.page_info.value = f"Всего заказов: {self.data['total']}"
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
                    ft.Text("№ Заказа", width=130, weight=ft.FontWeight.BOLD),
                    ft.Text("Авто ID", width=80, weight=ft.FontWeight.BOLD),
                    ft.Text("Статус", width=200, weight=ft.FontWeight.BOLD),
                    ft.Text("Работы", expand=True, weight=ft.FontWeight.BOLD),
                    ft.Text("Сумма", width=100, weight=ft.FontWeight.BOLD),
                    ft.Text("Действия", width=150, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            )
        )
        self.list_view.controls.append(ft.Divider())
        if not self.data["items"]:
            self.list_view.controls.append(ft.Container(content=ft.Text("Заказы не найдены", color=ft.Colors.GREY), padding=40, alignment=ft.alignment.center))
            return
        for o in self.data["items"]:
            status_label, status_color = STATUS_LABELS.get(o["status"], ("?", ft.Colors.GREY))
            row = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(o["order_number"], width=130, weight=ft.FontWeight.BOLD),
                        ft.Text(str(o["car_id"]), width=80),
                        ft.Container(content=ft.Text(status_label, size=12), bgcolor=status_color, color=ft.Colors.WHITE, padding=ft.padding.symmetric(4, 8), border_radius=4, width=200),
                        ft.Text(o["works_description"], expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"{o['amount']} ₽", width=100, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            [
                                ft.IconButton(icon=ft.Icons.EDIT, on_click=lambda e, oid=o["id"]: self._open_form(oid)),
                                ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_400, on_click=lambda e, oid=o["id"], n=o["order_number"]: self._delete(oid, n)),
                            ],
                            width=150,
                        ),
                    ],
                    spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=8, border_radius=6,
            )
            self.list_view.controls.append(row)

    async def _delete(self, order_id: int, number: str):
        def do_delete():
            self.page.run_task(self._do_delete, order_id)
        show_confirm_dialog(self.page, "Удаление заказа", f"Удалить заказ №{number}?", do_delete)

    async def _do_delete(self, order_id: int):
        try:
            await api.delete_order(order_id)
            await self._load()
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))

    def _open_form(self, order_id: int = None):
        dlg = OrderFormDialog(self.page, order_id, on_saved=lambda: self._load())
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()


class OrderFormDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page, order_id: int = None, on_saved=None):
        super().__init__(modal=True)
        self.page = page
        self.order_id = order_id
        self.on_saved = on_saved
        self.car_id = ft.TextField(label="ID автомобиля *", keyboard_type=ft.KeyboardType.NUMBER)
        self.works = ft.TextField(label="Описание работ *", multiline=True, min_lines=3, max_lines=6)
        self.amount = ft.TextField(label="Сумма (₽)", keyboard_type=ft.KeyboardType.NUMBER, value="0")
        self.status = ft.Dropdown(label="Статус", value="new", options=[ft.dropdown.Option(k, v[0]) for k, v in STATUS_LABELS.items()])
        self.title = ft.Text("Новый заказ" if not order_id else f"Заказ #{order_id}")
        self.content = ft.Column([self.car_id, self.works, self.amount, self.status], tight=True)
        self.actions = [
            ft.TextButton("Отмена", on_click=lambda e: self._close()),
            ft.ElevatedButton("Сохранить", on_click=lambda e: self._save()),
        ]
        if order_id:
            self.page.run_task(self._load_data)

    async def _load_data(self):
        try:
            data = await api.list_orders(page=1, page_size=1000)
            for o in data["items"]:
                if o["id"] == self.order_id:
                    self.car_id.value = str(o["car_id"])
                    self.works.value = o["works_description"]
                    self.amount.value = str(o["amount"])
                    self.status.value = o["status"]
                    self.page.update()
                    break
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))

    def _close(self):
        self.open = False
        self.page.update()

    async def _save(self):
        try:
            car_id = int(self.car_id.value)
        except ValueError:
            show_error_dialog(self.page, "Ошибка", "ID авто должен быть числом")
            return
        if not self.works.value.strip():
            show_error_dialog(self.page, "Ошибка", "Описание работ обязательно")
            return
        try:
            amount = float(self.amount.value or 0)
        except ValueError:
            show_error_dialog(self.page, "Ошибка", "Сумма должна быть числом")
            return
        payload = {
            "car_id": car_id,
            "works_description": self.works.value.strip(),
            "amount": amount,
            "status": self.status.value,
        }
        try:
            if self.order_id:
                await api.update_order(self.order_id, payload)
            else:
                await api.create_order(payload)
            self._close()
            if self.on_saved:
                self.on_saved()
        except Exception as e:
            show_error_dialog(self.page, "Ошибка сохранения", str(e))
