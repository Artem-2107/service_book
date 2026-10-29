from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class OrderCreate(BaseModel):
    car_id: int
    works_description: str = Field(..., min_length=5)
    amount: float = Field(0, ge=0)
    status: str = "new"


class OrderUpdate(BaseModel):
    car_id: Optional[int] = None
    works_description: Optional[str] = Field(None, min_length=5)
    amount: Optional[float] = Field(None, ge=0)
    status: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    order_number: str
    car_id: int
    status: str
    works_description: str
    amount: float
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderDetailResponse(BaseModel):
    """Заказ с полной информацией об авто и клиенте."""
    id: int
    order_number: str
    car_id: int
    car_brand: str
    car_model: str
    car_plate: str
    client_id: int
    client_fio: str
    status: str
    works_description: str
    amount: float
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaginatedOrders(BaseModel):
    items: List[OrderResponse]
    total: int
    page: int
    pages: int