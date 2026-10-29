from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ClientCreate(BaseModel):
    fio: str = Field(..., min_length=2, max_length=150)
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    fio: Optional[str] = Field(None, min_length=2, max_length=150)
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ClientResponse(BaseModel):
    id: int
    fio: str
    phone: Optional[str]
    email: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClientCarShort(BaseModel):
    id: int
    brand: str
    model: str
    plate: str
    year: Optional[int]

    class Config:
        from_attributes = True


class ClientOrderShort(BaseModel):
    id: int
    order_number: str
    car_plate: str
    status: str
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True


class ClientDetailResponse(BaseModel):
    """Клиент с историей: все его авто и заказы."""
    id: int
    fio: str
    phone: Optional[str]
    email: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    cars: List[ClientCarShort] = []
    orders: List[ClientOrderShort] = []
    total_orders: int = 0
    total_amount: float = 0.0

    class Config:
        from_attributes = True


class PaginatedClients(BaseModel):
    items: List[ClientResponse]
    total: int
    page: int
    pages: int