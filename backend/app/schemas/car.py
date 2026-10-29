from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CarCreate(BaseModel):
    client_id: int
    brand: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=50)
    plate: str = Field(..., min_length=1, max_length=20)
    vin: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=2100)
    notes: Optional[str] = None


class CarUpdate(BaseModel):
    client_id: Optional[int] = None
    brand: Optional[str] = Field(None, min_length=1, max_length=50)
    model: Optional[str] = Field(None, min_length=1, max_length=50)
    plate: Optional[str] = None
    vin: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=2100)
    notes: Optional[str] = None


class CarResponse(BaseModel):
    id: int
    client_id: int
    brand: str
    model: str
    plate: str
    vin: Optional[str]
    year: Optional[int]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CarOrderShort(BaseModel):
    id: int
    order_number: str
    status: str
    works_description: str
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True


class CarDetailResponse(BaseModel):
    """Авто с историей заказов."""
    id: int
    client_id: int
    client_fio: str
    brand: str
    model: str
    plate: str
    vin: Optional[str]
    year: Optional[int]
    notes: Optional[str]
    created_at: datetime
    orders: List[CarOrderShort] = []
    total_orders: int = 0
    total_amount: float = 0.0

    class Config:
        from_attributes = True


class PaginatedCars(BaseModel):
    items: List[CarResponse]
    total: int
    page: int
    pages: int