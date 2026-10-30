import httpx
from typing import Optional, Any, Dict
from config import API_BASE_URL


class ApiClient:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.token: Optional[str] = None

    def set_token(self, token: str) -> None:
        self.token = token.strip()

    def clear_token(self) -> None:
        self.token = None

    def _get_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None,
                       json_data: Optional[Dict[str, Any]] = None) -> httpx.Response:
        url = f"{self.base_url}{path}"
        headers = self._get_headers()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.request(method, url, headers=headers, params=params, json=json_data)
            return response
        except httpx.ConnectError as e:
            raise ConnectionError(f"Не удалось подключиться к серверу {self.base_url}. Проверьте, что backend запущен и телефон в той же Wi-Fi сети. Ошибка: {str(e)}")
        except Exception as e:
            raise Exception(f"Ошибка сети: {str(e)}")

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        try:
            response = await self._request("POST", "/auth/login", json_data={"username": username, "password": password})
            if response.status_code != 200:
                raise ValueError(response.json().get("detail", "Ошибка входа"))
            data = response.json()
            self.set_token(data["access_token"])
            return data
        except ConnectionError:
            raise
        except Exception as e:
            raise ValueError(f"Ошибка входа: {str(e)}")

    async def register(self, data: Dict[str, Any]) -> Dict[str, Any]:
        response = await self._request("POST", "/auth/register", json_data=data)
        if response.status_code not in (200, 201):
            raise ValueError(response.json().get("detail", "Ошибка регистрации"))
        return response.json()

    async def list_clients(self, page: int = 1, page_size: int = 20, search: Optional[str] = None):
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        response = await self._request("GET", "/clients/", params=params)
        if response.status_code != 200:
            raise ValueError(response.json().get("detail", "Ошибка"))
        return response.json()

    async def get_client_detail(self, client_id: int):
        response = await self._request("GET", f"/clients/{client_id}")
        if response.status_code != 200:
            raise ValueError(response.json().get("detail", "Ошибка"))
        return response.json()

    async def create_client(self, data: Dict[str, Any]):
        response = await self._request("POST", "/clients/", json_data=data)
        if response.status_code not in (200, 201):
            raise ValueError(response.json().get("detail", "Ошибка"))
        return response.json()

    async def update_client(self, client_id: int, data: Dict[str, Any]):
        response = await self._request("PATCH", f"/clients/{client_id}", json_data=data)
        if response.status_code != 200:
            raise ValueError(response.json().get("detail", "Ошибка"))
        return response.json()

    async def delete_client(self, client_id: int):
        response = await self._request("DELETE", f"/clients/{client_id}")
        if response.status_code not in (200, 204):
            raise ValueError(response.json().get("detail", "Ошибка"))

    async def list_cars(self, page: int = 1, page_size: int = 20, search: Optional[str] = None,
                        client_id: Optional[int] = None):
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        if client_id:
            params["client_id"] = client_id
        response = await self._request("GET", "/cars/", params=params)
        if response.status_code != 200:
            raise ValueError(response.json().get("detail", "Ошибка"))
        return response.json()

    async def get_car_detail(self, car_id: int):
        response = await self._request("GET", f"/cars/{car_id}")
        if response.status_code != 200:
            raise ValueError(response.json().get("detail", "Ошибка"))
        return response.json()

    async def create_car(self, data: Dict[str, Any]):
        response = await self._request("POST", "/cars/", json_data=data)
        if response.status_code not in (200, 201):
            raise ValueError(response.json().get("detail", "Ошибка"))
        return response.json()

    async def update_car(self, car_id: int, data: Dict[str, Any]):
        response = await self._request("PATCH", f"/cars/{car_id}", json_data=data)
        if response.status_code != 200:
            raise ValueError(response.json().get("detail", "Ошибка"))
        return response.json()

    async def delete_car(self, car_id: int):
        response = await self._request("DELETE", f"/cars/{car_id}")
        if response.status_code not in (200, 204):
            raise ValueError(response.json().get("detail", "Ошибка"))

    async def list_orders(self, page: int = 1, page_size: int = 20, status: Optional[str] = None,
                          car_id: Optional[int] = None):
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        if car_id:
            params["car_id"] = car_id
        response = await self._request("GET", "/orders/", params=params)
        if response.status_code != 200:
            raise ValueError(response.json().get("detail", "Ошибка"))
        return response.json()

    async def get_order_detail(self, order_id: int):
        response = await self._request("GET", f"/orders/{order_id}")
        if response.status_code != 200:
            raise ValueError(response.json().get("detail", "Ошибка"))
        return response.json()

    async def create_order(self, data: Dict[str, Any]):
        response = await self._request("POST", "/orders/", json_data=data)
        if response.status_code not in (200, 201):
            raise ValueError(response.json().get("detail", "Ошибка"))
        return response.json()

    async def update_order(self, order_id: int, data: Dict[str, Any]):
        response = await self._request("PATCH", f"/orders/{order_id}", json_data=data)
        if response.status_code != 200:
            raise ValueError(response.json().get("detail", "Ошибка"))
        return response.json()

    async def delete_order(self, order_id: int):
        response = await self._request("DELETE", f"/orders/{order_id}")
        if response.status_code not in (200, 204):
            raise ValueError(response.json().get("detail", "Ошибка"))

    async def get_stats(self):
        response = await self._request("GET", "/stats/")
        if response.status_code != 200:
            raise ValueError(response.json().get("detail", "Ошибка"))
        return response.json()


api = ApiClient()