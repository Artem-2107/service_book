import flet as ft
from api_client import api
from components.dialogs import show_error_dialog, show_success_dialog, show_confirm_dialog, show_error_with_retry


class MainScreen:
    def __init__(self, page: ft.Page, user_data: dict, on_logout):
        self.page = page
        self.user_data = user_data or {}
        self.on_logout = on_logout
        self.content = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
        
        self.role = self.user_data.get("role", "user")
        self.is_accountant = (self.role == "accountant")
        
        self.clients_data = {"items": [], "total": 0, "pages": 0}
        self.client_page = 1
        self.client_search = ""
        
        self.cars_data = {"items": [], "total": 0, "pages": 0}
        self.car_page = 1
        self.car_search = ""
        
        self.orders_data = {"items": [], "total": 0, "pages": 0}
        self.order_page = 1
        self.order_status = None  # None = показать все
        
        self.stats_data = None

    def get_app_bar(self):
        full_name = self.user_data.get("full_name", "")
        username = self.user_data.get("username", "")
        role_labels = {"admin": "Админ", "manager": "Мастер", "accountant": "Бухгалтер"}
        role_label = role_labels.get(self.role, self.role)
        
        return ft.AppBar(
            title=ft.Text("ServiceBook", size=18),
            bgcolor=ft.Colors.BLUE_GREY_900,
            actions=[
                ft.Column([
                    ft.Text(full_name or username, size=11, color=ft.Colors.WHITE, text_align=ft.TextAlign.RIGHT),
                    ft.Text(role_label, size=10, color=ft.Colors.GREY_400, text_align=ft.TextAlign.RIGHT),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.VerticalDivider(),
                ft.IconButton(icon=ft.Icons.LOGOUT, icon_size=20, on_click=lambda e: self._logout()),
            ],
        )

    def build(self):
        self.content.controls.clear()
        self.content.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.HOME, size=48, color=ft.Colors.BLUE),
                    ft.Text("ServiceBook", size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text("Главное меню", size=13, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
                    ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                    self._build_stats_placeholder(),
                    ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                    ft.ElevatedButton("👥 Клиенты", width=280, height=48, on_click=lambda e: self._show_clients()),
                    ft.ElevatedButton("🚗 Автомобили", width=280, height=48, on_click=lambda e: self._show_cars()),
                    ft.ElevatedButton("📋 Заказы", width=280, height=48, on_click=lambda e: self._show_orders()),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                expand=True, alignment=ft.alignment.center,
            )
        )
        self.page.update()
        self.page.run_task(self._load_stats)
        return self.content

    def _build_stats_placeholder(self):
        self.stats_container = ft.Row([
            self._stat_card("Клиенты", "...", ft.Icons.PERSON, ft.Colors.BLUE),
            self._stat_card("Авто", "...", ft.Icons.DIRECTIONS_CAR, ft.Colors.GREEN),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10, wrap=True)
        self.stats_container2 = ft.Row([
            self._stat_card("Заказы", "...", ft.Icons.RECEIPT, ft.Colors.ORANGE),
            self._stat_card("Выручка", "...", ft.Icons.MONETIZATION_ON, ft.Colors.PURPLE),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10, wrap=True)
        return ft.Column([self.stats_container, self.stats_container2], spacing=10)

    def _stat_card(self, title, value, icon, color):
        return ft.Container(
            width=170, padding=12, border_radius=10, bgcolor=ft.Colors.GREY_800,
            content=ft.Column([
                ft.Icon(icon, size=28, color=color),
                ft.Text(value, size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Text(title, size=11, color=ft.Colors.GREY, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )

    async def _load_stats(self):
        try:
            self.stats_data = await api.get_stats()
            self.stats_container.controls = [
                self._stat_card("Клиенты", str(self.stats_data["total_clients"]), ft.Icons.PERSON, ft.Colors.BLUE),
                self._stat_card("Авто", str(self.stats_data["total_cars"]), ft.Icons.DIRECTIONS_CAR, ft.Colors.GREEN),
            ]
            self.stats_container2.controls = [
                self._stat_card("Заказы", str(self.stats_data["total_orders"]), ft.Icons.RECEIPT, ft.Colors.ORANGE),
                self._stat_card("Выручка", f"{self.stats_data['total_revenue']:,.0f}₽", ft.Icons.MONETIZATION_ON, ft.Colors.PURPLE),
            ]
            self.page.update()
        except Exception as e:
            self.stats_container.controls = [
                self._stat_card("Клиенты", "—", ft.Icons.PERSON, ft.Colors.GREY),
                self._stat_card("Авто", "—", ft.Icons.DIRECTIONS_CAR, ft.Colors.GREY),
            ]
            self.stats_container2.controls = [
                self._stat_card("Заказы", "—", ft.Icons.RECEIPT, ft.Colors.GREY),
                self._stat_card("Выручка", "—", ft.Icons.MONETIZATION_ON, ft.Colors.GREY),
            ]
            self.page.update()
            show_error_with_retry(
                self.page, "Не удалось загрузить статистику",
                f"Ошибка: {str(e)}",
                lambda: self.page.run_task(self._load_stats)
            )

    # ===== КЛИЕНТЫ =====
    def _show_clients(self):
        self.client_page = 1
        self.client_search = ""
        self.content.controls.clear()
        self.content.controls.append(ft.Row([
            ft.Text("👥 Клиенты", size=20, weight=ft.FontWeight.BOLD, expand=True),
            ft.ElevatedButton("← Назад", height=36, on_click=lambda e: self._show_menu()),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        
        self.search_field = ft.TextField(hint_text="Поиск по ФИО...", prefix_icon=ft.Icons.SEARCH, expand=True,
                                         on_submit=lambda e: self.page.run_task(self._search_clients))
        self.content.controls.append(ft.Row([
            self.search_field,
            ft.IconButton(icon=ft.Icons.SEARCH, on_click=lambda e: self.page.run_task(self._search_clients)),
        ], spacing=4))
        
        action_row_controls = []
        if not self.is_accountant:
            action_row_controls.append(ft.ElevatedButton("➕ Добавить", icon=ft.Icons.ADD, height=40, on_click=lambda e: self._open_client_form()))
        action_row_controls.append(ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Обновить", on_click=lambda e: self.page.run_task(self._load_clients)))
        
        self.content.controls.append(ft.Row(action_row_controls, alignment=ft.MainAxisAlignment.END, spacing=8))
        
        self.client_info = ft.Text("Загрузка...", size=11, color=ft.Colors.GREY)
        self.content.controls.append(self.client_info)
        self.content.controls.append(ft.Divider())
        self.clients_list = ft.Column(spacing=6, expand=True)
        self.content.controls.append(self.clients_list)
        self.pagination = ft.Row([
            ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, icon_size=20, on_click=lambda e: self.page.run_task(self._prev_client_page)),
            ft.Text("Стр. 1", size=12),
            ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, icon_size=20, on_click=lambda e: self.page.run_task(self._next_client_page)),
        ], alignment=ft.MainAxisAlignment.CENTER)
        self.content.controls.append(self.pagination)
        self.page.update()
        self.page.run_task(self._load_clients)

    async def _load_clients(self):
        self.client_info.value = "Обновление..."
        self.page.update()
        try:
            self.clients_data = await api.list_clients(page=self.client_page, page_size=15, search=self.client_search or None)
            self._render_clients()
            self.client_info.value = f"Всего: {self.clients_data['total']} | Стр. {self.clients_data['page']} из {self.clients_data['pages']}"
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))
        finally:
            self.page.update()

    def _render_clients(self):
        self.clients_list.controls.clear()
        if not self.clients_data["items"]:
            self.clients_list.controls.append(ft.Container(content=ft.Text("Ничего не найдено", color=ft.Colors.GREY), padding=20, alignment=ft.alignment.center))
            return
        for c in self.clients_data["items"]:
            action_buttons = [
                ft.IconButton(icon=ft.Icons.VISIBILITY, icon_size=20, tooltip="Подробнее", on_click=lambda e, cid=c["id"]: self.page.run_task(self._show_client_detail, cid)),
            ]
            if not self.is_accountant:
                action_buttons.append(ft.IconButton(icon=ft.Icons.EDIT, icon_size=20, on_click=lambda e, cid=c["id"]: self._open_client_form(cid)))
                action_buttons.append(ft.IconButton(icon=ft.Icons.DELETE, icon_size=20, icon_color=ft.Colors.RED_400, on_click=lambda e, cid=c["id"], fio=c["fio"]: self.page.run_task(self._delete_client, cid, fio)))
            
            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"#{c['id']}", size=12, color=ft.Colors.GREY),
                        ft.Text(c["fio"], size=14, weight=ft.FontWeight.W_600, expand=True),
                    ]),
                    ft.Row([
                        ft.Text(f"📞 {c.get('phone') or '—'}", size=12, color=ft.Colors.GREY),
                        ft.Text(f"✉️ {c.get('email') or '—'}", size=12, color=ft.Colors.GREY, expand=True),
                    ]),
                    ft.Row(action_buttons, alignment=ft.MainAxisAlignment.END, spacing=4),
                ], spacing=4),
                padding=10, border_radius=8, bgcolor=ft.Colors.GREY_800,
            )
            self.clients_list.controls.append(card)

    async def _show_client_detail(self, client_id: int):
        try:
            detail = await api.get_client_detail(client_id)
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))
            return
        
        self.content.controls.clear()
        self.content.controls.append(ft.Row([
            ft.Text(f"👤 {detail['fio']}", size=18, weight=ft.FontWeight.BOLD, expand=True),
            ft.ElevatedButton("← Назад", height=36, on_click=lambda e: self._show_clients()),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        
        self.content.controls.append(ft.Container(
            content=ft.Column([
                ft.Text(f"📞 {detail.get('phone') or '—'}", size=13),
                ft.Text(f"✉️ {detail.get('email') or '—'}", size=13),
                ft.Text(f" {detail.get('notes') or '—'}", size=13),
                ft.Divider(),
                ft.Row([
                    ft.Text(f" {len(detail['cars'])}", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(f"📋 {detail['total_orders']}", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(f"💰 {detail['total_amount']:,.0f}₽", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ], spacing=6),
            padding=12, border_radius=8, bgcolor=ft.Colors.GREY_800,
        ))
        
        self.content.controls.append(ft.Text("🚗 Автомобили:", size=16, weight=ft.FontWeight.BOLD))
        if detail["cars"]:
            for car in detail["cars"]:
                self.content.controls.append(ft.Container(
                    content=ft.Text(f"{car['brand']} {car['model']} | {car['plate']} | {car.get('year') or '—'} г.", size=13),
                    padding=8, border_radius=6, bgcolor=ft.Colors.GREY_800,
                ))
        else:
            self.content.controls.append(ft.Text("Нет автомобилей", color=ft.Colors.GREY, size=12))
        
        self.content.controls.append(ft.Divider())
        self.content.controls.append(ft.Text("📋 История заказов:", size=16, weight=ft.FontWeight.BOLD))
        if detail["orders"]:
            status_labels = {"new": "🆕 Новый", "in_progress": "🔧 В работе", "done": "✅ Готов", "issued": " Выдан"}
            for o in detail["orders"]:
                self.content.controls.append(ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(o["order_number"], size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(status_labels.get(o["status"], o["status"]), size=12),
                            ft.Text(f"{o['amount']:,.0f}₽", size=12, color=ft.Colors.GREEN),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(o["car_plate"], size=11, color=ft.Colors.GREY),
                        ft.Text(o["created_at"][:10], size=11, color=ft.Colors.GREY),
                    ], spacing=2),
                    padding=8, border_radius=6, bgcolor=ft.Colors.GREY_800,
                ))
        else:
            self.content.controls.append(ft.Text("Нет заказов", color=ft.Colors.GREY, size=12))
        
        self.page.update()

    async def _search_clients(self):
        self.client_search = self.search_field.value.strip()
        self.client_page = 1
        await self._load_clients()

    async def _prev_client_page(self):
        if self.client_page > 1:
            self.client_page -= 1
            await self._load_clients()

    async def _next_client_page(self):
        if self.client_page < self.clients_data.get("pages", 1):
            self.client_page += 1
            await self._load_clients()

    async def _delete_client(self, client_id: int, fio: str):
        def do_delete(): self.page.run_task(self._do_delete_client, client_id)
        show_confirm_dialog(self.page, "Удаление", f"Удалить '{fio}'? Все авто и заказы будут удалены!", do_delete)

    async def _do_delete_client(self, client_id: int):
        try:
            await api.delete_client(client_id)
            await self._load_clients()
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))

    def _open_client_form(self, client_id: int = None):
        dlg = ClientFormDialog(self.page, client_id, on_saved=lambda: self.page.run_task(self._load_clients))
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    # ===== АВТОМОБИЛИ =====
    def _show_cars(self):
        self.car_page = 1
        self.car_search = ""
        self.content.controls.clear()
        self.content.controls.append(ft.Row([
            ft.Text(" Автомобили", size=20, weight=ft.FontWeight.BOLD, expand=True),
            ft.ElevatedButton("← Назад", height=36, on_click=lambda e: self._show_menu()),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        
        self.car_search_field = ft.TextField(hint_text="Поиск по госномеру...", prefix_icon=ft.Icons.SEARCH, expand=True,
                                             on_submit=lambda e: self.page.run_task(self._search_cars))
        self.content.controls.append(ft.Row([
            self.car_search_field,
            ft.IconButton(icon=ft.Icons.SEARCH, on_click=lambda e: self.page.run_task(self._search_cars)),
        ], spacing=4))
        
        action_row_controls = []
        if not self.is_accountant:
            action_row_controls.append(ft.ElevatedButton("➕ Добавить", icon=ft.Icons.ADD, height=40, on_click=lambda e: self._open_car_form()))
        action_row_controls.append(ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Обновить", on_click=lambda e: self.page.run_task(self._load_cars)))
        
        self.content.controls.append(ft.Row(action_row_controls, alignment=ft.MainAxisAlignment.END, spacing=8))
        
        self.car_info = ft.Text("Загрузка...", size=11, color=ft.Colors.GREY)
        self.content.controls.append(self.car_info)
        self.content.controls.append(ft.Divider())
        self.cars_list = ft.Column(spacing=6, expand=True)
        self.content.controls.append(self.cars_list)
        self.car_pagination = ft.Row([
            ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, icon_size=20, on_click=lambda e: self.page.run_task(self._prev_car_page)),
            ft.Text("Стр. 1", size=12),
            ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, icon_size=20, on_click=lambda e: self.page.run_task(self._next_car_page)),
        ], alignment=ft.MainAxisAlignment.CENTER)
        self.content.controls.append(self.car_pagination)
        self.page.update()
        self.page.run_task(self._load_cars)

    async def _load_cars(self):
        self.car_info.value = "Обновление..."
        self.page.update()
        try:
            self.cars_data = await api.list_cars(page=self.car_page, page_size=15, search=self.car_search or None)
            self._render_cars()
            self.car_info.value = f"Всего: {self.cars_data['total']} | Стр. {self.cars_data['page']} из {self.cars_data['pages']}"
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))
        finally:
            self.page.update()

    def _render_cars(self):
        self.cars_list.controls.clear()
        if not self.cars_data["items"]:
            self.cars_list.controls.append(ft.Container(content=ft.Text("Ничего не найдено", color=ft.Colors.GREY), padding=20, alignment=ft.alignment.center))
            return
        for c in self.cars_data["items"]:
            action_buttons = [
                ft.IconButton(icon=ft.Icons.VISIBILITY, icon_size=20, tooltip="Подробнее", on_click=lambda e, cid=c["id"]: self.page.run_task(self._show_car_detail, cid)),
            ]
            if not self.is_accountant:
                action_buttons.append(ft.IconButton(icon=ft.Icons.EDIT, icon_size=20, on_click=lambda e, cid=c["id"]: self._open_car_form(cid)))
                action_buttons.append(ft.IconButton(icon=ft.Icons.DELETE, icon_size=20, icon_color=ft.Colors.RED_400, on_click=lambda e, cid=c["id"], p=c["plate"]: self.page.run_task(self._delete_car, cid, p)))
            
            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"#{c['id']}", size=12, color=ft.Colors.GREY),
                        ft.Text(f"{c['brand']} {c['model']}", size=14, weight=ft.FontWeight.W_600, expand=True),
                    ]),
                    ft.Row([
                        ft.Text(f"🔢 {c['plate']}", size=12, color=ft.Colors.GREY),
                        ft.Text(f"📅 {c.get('year') or '—'}", size=12, color=ft.Colors.GREY),
                    ]),
                    ft.Text(f"VIN: {c.get('vin') or '—'}", size=11, color=ft.Colors.GREY_600),
                    ft.Row(action_buttons, alignment=ft.MainAxisAlignment.END, spacing=4),
                ], spacing=4),
                padding=10, border_radius=8, bgcolor=ft.Colors.GREY_800,
            )
            self.cars_list.controls.append(card)

    async def _show_car_detail(self, car_id: int):
        try:
            detail = await api.get_car_detail(car_id)
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))
            return
        
        self.content.controls.clear()
        self.content.controls.append(ft.Row([
            ft.Text(f" {detail['brand']} {detail['model']}", size=18, weight=ft.FontWeight.BOLD, expand=True),
            ft.ElevatedButton("← Назад", height=36, on_click=lambda e: self._show_cars()),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        
        self.content.controls.append(ft.Container(
            content=ft.Column([
                ft.Text(f"🔢 {detail['plate']}", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(f" {detail['client_fio']}", size=13),
                ft.Text(f"VIN: {detail.get('vin') or '—'}", size=13),
                ft.Text(f"📅 {detail.get('year') or '—'} г.", size=13),
                ft.Text(f" {detail.get('notes') or '—'}", size=13),
                ft.Divider(),
                ft.Row([
                    ft.Text(f" {detail['total_orders']}", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(f"💰 {detail['total_amount']:,.0f}₽", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ], spacing=6),
            padding=12, border_radius=8, bgcolor=ft.Colors.GREY_800,
        ))
        
        self.content.controls.append(ft.Divider())
        self.content.controls.append(ft.Text("📋 История заказов:", size=16, weight=ft.FontWeight.BOLD))
        if detail["orders"]:
            status_labels = {"new": "🆕 Новый", "in_progress": "🔧 В работе", "done": "✅ Готов", "issued": " Выдан"}
            for o in detail["orders"]:
                self.content.controls.append(ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(o["order_number"], size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(status_labels.get(o["status"], o["status"]), size=12),
                            ft.Text(f"{o['amount']:,.0f}₽", size=12, color=ft.Colors.GREEN),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(o["works_description"], size=12, color=ft.Colors.GREY),
                        ft.Text(o["created_at"][:10], size=11, color=ft.Colors.GREY_600),
                    ], spacing=2),
                    padding=8, border_radius=6, bgcolor=ft.Colors.GREY_800,
                ))
        else:
            self.content.controls.append(ft.Text("Нет заказов", color=ft.Colors.GREY, size=12))
        
        self.page.update()

    async def _search_cars(self):
        self.car_search = self.car_search_field.value.strip()
        self.car_page = 1
        await self._load_cars()

    async def _prev_car_page(self):
        if self.car_page > 1:
            self.car_page -= 1
            await self._load_cars()

    async def _next_car_page(self):
        if self.car_page < self.cars_data.get("pages", 1):
            self.car_page += 1
            await self._load_cars()

    async def _delete_car(self, car_id: int, plate: str):
        def do_delete(): self.page.run_task(self._do_delete_car, car_id)
        show_confirm_dialog(self.page, "Удаление", f"Удалить авто {plate}?", do_delete)

    async def _do_delete_car(self, car_id: int):
        try:
            await api.delete_car(car_id)
            await self._load_cars()
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))

    def _open_car_form(self, car_id: int = None):
        dlg = CarFormDialog(self.page, car_id, on_saved=lambda: self.page.run_task(self._load_cars))
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    # ===== ЗАКАЗЫ =====
    def _show_orders(self):
        self.order_page = 1
        self.order_status = None  # Сброс фильтра — показать все
        self.content.controls.clear()
        self.content.controls.append(ft.Row([
            ft.Text("📋 Заказы", size=20, weight=ft.FontWeight.BOLD, expand=True),
            ft.ElevatedButton("← Назад", height=36, on_click=lambda e: self._show_menu()),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        
        # Фильтр по статусу — используем "all" вместо "" для пункта "Все"
        self.status_filter = ft.Dropdown(
            label="Статус",
            width=200,
            value="all",  # По умолчанию — все
            options=[
                ft.dropdown.Option("all", "— Все —"),
                ft.dropdown.Option("new", "🆕 Новый"),
                ft.dropdown.Option("in_progress", "🔧 В работе"),
                ft.dropdown.Option("done", "✅ Готов"),
                ft.dropdown.Option("issued", " Выдан"),
            ],
            on_change=lambda e: self.page.run_task(self._filter_orders)
        )
        
        filter_row = ft.Row([self.status_filter], expand=True)
        self.content.controls.append(filter_row)
        
        action_row_controls = []
        if not self.is_accountant:
            action_row_controls.append(ft.IconButton(icon=ft.Icons.ADD, tooltip="Новый заказ", on_click=lambda e: self._open_order_form()))
        action_row_controls.append(ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Обновить", on_click=lambda e: self.page.run_task(self._load_orders)))
        
        self.content.controls.append(ft.Row(action_row_controls, alignment=ft.MainAxisAlignment.END, spacing=8))
        
        self.order_info = ft.Text("Загрузка...", size=11, color=ft.Colors.GREY)
        self.content.controls.append(self.order_info)
        self.content.controls.append(ft.Divider())
        self.orders_list = ft.Column(spacing=6, expand=True)
        self.content.controls.append(self.orders_list)
        self.order_pagination = ft.Row([
            ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, icon_size=20, on_click=lambda e: self.page.run_task(self._prev_order_page)),
            ft.Text("Стр. 1", size=12),
            ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, icon_size=20, on_click=lambda e: self.page.run_task(self._next_order_page)),
        ], alignment=ft.MainAxisAlignment.CENTER)
        self.content.controls.append(self.order_pagination)
        self.page.update()
        self.page.run_task(self._load_orders)

    async def _load_orders(self):
        self.order_info.value = "Обновление..."
        self.page.update()
        try:
            # Если order_status == "all" или None — не передаём фильтр
            status_param = None if (self.order_status is None or self.order_status == "all") else self.order_status
            self.orders_data = await api.list_orders(page=self.order_page, page_size=15, status=status_param)
            self._render_orders()
            self.order_info.value = f"Всего: {self.orders_data['total']} | Стр. {self.orders_data['page']} из {self.orders_data['pages']}"
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))
        finally:
            self.page.update()

    def _render_orders(self):
        self.orders_list.controls.clear()
        if not self.orders_data["items"]:
            self.orders_list.controls.append(ft.Container(content=ft.Text("Ничего не найдено", color=ft.Colors.GREY), padding=20, alignment=ft.alignment.center))
            return
        status_labels = {"new": "🆕 Новый", "in_progress": "🔧 В работе", "done": "✅ Готов", "issued": " Выдан"}
        for o in self.orders_data["items"]:
            action_buttons = [
                ft.IconButton(icon=ft.Icons.VISIBILITY, icon_size=20, tooltip="Подробнее", on_click=lambda e, oid=o["id"]: self.page.run_task(self._show_order_detail, oid)),
            ]
            if not self.is_accountant:
                action_buttons.append(ft.IconButton(icon=ft.Icons.EDIT, icon_size=20, on_click=lambda e, oid=o["id"]: self._open_order_form(oid)))
                action_buttons.append(ft.IconButton(icon=ft.Icons.DELETE, icon_size=20, icon_color=ft.Colors.RED_400, on_click=lambda e, oid=o["id"], n=o["order_number"]: self.page.run_task(self._delete_order, oid, n)))
            
            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(o["order_number"], size=12, weight=ft.FontWeight.BOLD),
                        ft.Text(status_labels.get(o["status"], o["status"]), size=12),
                        ft.Text(f"{o['amount']:,.0f}₽", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(f" Авто ID: {o['car_id']}", size=11, color=ft.Colors.GREY),
                    ft.Text(o["works_description"], size=12, max_lines=2),
                    ft.Row(action_buttons, alignment=ft.MainAxisAlignment.END, spacing=4),
                ], spacing=4),
                padding=10, border_radius=8, bgcolor=ft.Colors.GREY_800,
            )
            self.orders_list.controls.append(card)

    async def _show_order_detail(self, order_id: int):
        try:
            detail = await api.get_order_detail(order_id)
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))
            return
        
        self.content.controls.clear()
        self.content.controls.append(ft.Row([
            ft.Text(f"📋 №{detail['order_number']}", size=18, weight=ft.FontWeight.BOLD, expand=True),
            ft.ElevatedButton("← Назад", height=36, on_click=lambda e: self._show_orders()),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        
        status_labels = {"new": "🆕 Новый", "in_progress": "🔧 В работе", "done": "✅ Готов", "issued": "📦 Выдан"}
        
        self.content.controls.append(ft.Container(
            content=ft.Column([
                ft.Text(f"👤 {detail['client_fio']}", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(f" {detail['car_brand']} {detail['car_model']} | {detail['car_plate']}", size=13),
                ft.Divider(),
                ft.Text(f"📊 {status_labels.get(detail['status'], detail['status'])}", size=14),
                ft.Text("🔧 Работы:", size=13, weight=ft.FontWeight.BOLD),
                ft.Text(detail["works_description"], size=13),
                ft.Divider(),
                ft.Row([
                    ft.Text(f"💰 {detail['amount']:,.0f}₽", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                    ft.Text(f"📅 {detail['created_at'][:10]}", size=12, color=ft.Colors.GREY),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=6),
            padding=12, border_radius=8, bgcolor=ft.Colors.GREY_800,
        ))
        self.page.update()

    async def _filter_orders(self):
        # Получаем значение из Dropdown
        selected = self.status_filter.value
        # Если "all" — сбрасываем фильтр (None), иначе передаём статус
        self.order_status = None if selected == "all" else selected
        self.order_page = 1
        await self._load_orders()

    async def _prev_order_page(self):
        if self.order_page > 1:
            self.order_page -= 1
            await self._load_orders()

    async def _next_order_page(self):
        if self.order_page < self.orders_data.get("pages", 1):
            self.order_page += 1
            await self._load_orders()

    async def _delete_order(self, order_id: int, number: str):
        def do_delete(): self.page.run_task(self._do_delete_order, order_id)
        show_confirm_dialog(self.page, "Удаление", f"Удалить заказ №{number}?", do_delete)

    async def _do_delete_order(self, order_id: int):
        try:
            await api.delete_order(order_id)
            await self._load_orders()
        except Exception as e:
            show_error_dialog(self.page, "Ошибка", str(e))

    def _open_order_form(self, order_id: int = None):
        dlg = OrderFormDialog(self.page, order_id, on_saved=lambda: self.page.run_task(self._load_orders))
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    # ===== НАВИГАЦИЯ =====
    def _show_menu(self):
        self.page.clean()
        main_screen = MainScreen(self.page, self.user_data, self.on_logout)
        self.page.appbar = main_screen.get_app_bar()
        self.page.add(main_screen.build())
        self.page.update()

    def _logout(self):
        api.clear_token()
        self.on_logout()


# ===== ДИАЛОГИ ФОРМ =====
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
        self.title = ft.Text("Новый клиент" if not client_id else "Редактирование")
        self.content = ft.Column([self.fio, self.phone, self.email, self.notes], tight=True, scroll=ft.ScrollMode.AUTO)
        self.actions = [
            ft.TextButton("Отмена", on_click=lambda e: self._close()),
            ft.ElevatedButton("Сохранить", on_click=lambda e: self.page.run_task(self._save)),
        ]
        if client_id:
            self.page.run_task(self._load_data)

    async def _load_data(self):
        try:
            data = await api.list_clients(page=1, page_size=100)
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
        payload = {"fio": self.fio.value.strip(), "phone": self.phone.value.strip() or None,
                   "email": self.email.value.strip() or None, "notes": self.notes.value.strip() or None}
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


class CarFormDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page, car_id: int = None, on_saved=None):
        super().__init__(modal=True)
        self.page = page
        self.car_id = car_id
        self.on_saved = on_saved
        self.client_id_field = ft.TextField(label="ID клиента *", keyboard_type=ft.KeyboardType.NUMBER)
        self.brand = ft.TextField(label="Марка *")
        self.model = ft.TextField(label="Модель *")
        self.plate = ft.TextField(label="Госномер *")
        self.vin = ft.TextField(label="VIN (17 символов)", max_length=17)
        self.year = ft.TextField(label="Год выпуска", keyboard_type=ft.KeyboardType.NUMBER)
        self.notes = ft.TextField(label="Заметки", multiline=True, min_lines=2)
        self.title = ft.Text("Новый автомобиль" if not car_id else "Редактирование")
        self.content = ft.Column([self.client_id_field, self.brand, self.model, self.plate, self.vin, self.year, self.notes], tight=True, scroll=ft.ScrollMode.AUTO)
        self.actions = [
            ft.TextButton("Отмена", on_click=lambda e: self._close()),
            ft.ElevatedButton("Сохранить", on_click=lambda e: self.page.run_task(self._save)),
        ]
        if car_id:
            self.page.run_task(self._load_data)

    async def _load_data(self):
        try:
            data = await api.list_cars(page=1, page_size=100)
            for c in data["items"]:
                if c["id"] == self.car_id:
                    self.client_id_field.value = str(c["client_id"])
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
            client_id = int(self.client_id_field.value)
        except ValueError:
            show_error_dialog(self.page, "Ошибка", "ID клиента должен быть числом")
            return
        if not all([self.brand.value, self.model.value, self.plate.value]):
            show_error_dialog(self.page, "Ошибка", "Заполните обязательные поля")
            return
        payload = {"client_id": client_id, "brand": self.brand.value.strip(), "model": self.model.value.strip(),
                   "plate": self.plate.value.strip(), "vin": self.vin.value.strip() or None,
                   "year": int(self.year.value) if self.year.value.strip() else None,
                   "notes": self.notes.value.strip() or None}
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


class OrderFormDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page, order_id: int = None, on_saved=None):
        super().__init__(modal=True)
        self.page = page
        self.order_id = order_id
        self.on_saved = on_saved
        self.car_id_field = ft.TextField(label="ID автомобиля *", keyboard_type=ft.KeyboardType.NUMBER)
        self.works = ft.TextField(label="Описание работ *", multiline=True, min_lines=3, max_lines=6)
        self.amount = ft.TextField(label="Сумма (₽)", keyboard_type=ft.KeyboardType.NUMBER, value="0")
        self.status = ft.Dropdown(label="Статус", value="new",
            options=[ft.dropdown.Option("new", "Новый"), ft.dropdown.Option("in_progress", "В работе"),
                     ft.dropdown.Option("done", "Готов"), ft.dropdown.Option("issued", "Выдан")])
        self.title = ft.Text("Новый заказ" if not order_id else f"Заказ #{order_id}")
        self.content = ft.Column([self.car_id_field, self.works, self.amount, self.status], tight=True, scroll=ft.ScrollMode.AUTO)
        self.actions = [
            ft.TextButton("Отмена", on_click=lambda e: self._close()),
            ft.ElevatedButton("Сохранить", on_click=lambda e: self.page.run_task(self._save)),
        ]
        if order_id:
            self.page.run_task(self._load_data)

    async def _load_data(self):
        try:
            data = await api.list_orders(page=1, page_size=100)
            for o in data["items"]:
                if o["id"] == self.order_id:
                    self.car_id_field.value = str(o["car_id"])
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
            car_id = int(self.car_id_field.value)
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
        payload = {"car_id": car_id, "works_description": self.works.value.strip(),
                   "amount": amount, "status": self.status.value}
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