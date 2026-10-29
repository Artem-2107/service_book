from pydantic import BaseModel
from typing import Optional


class StatsResponse(BaseModel):
    total_clients: int
    total_cars: int
    total_orders: int
    total_revenue: float
    orders_by_status: dict
    recent_orders_count: int  # за последние 30 дней