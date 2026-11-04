from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import require_manager_or_admin, require_any_authenticated
from app.services.order_service import OrderService
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderDetailResponse, PaginatedOrders


router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=PaginatedOrders)
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    car_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_any_authenticated),
):
    service = OrderService(db)
    return await service.list(page, page_size, status, car_id)


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order_detail(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_any_authenticated),
):
    """Полная информация о заказе с данными авто и клиента."""
    service = OrderService(db)
    return await service.get_detail(order_id)


@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_manager_or_admin),
):
    service = OrderService(db)
    return await service.create(data)


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    data: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_manager_or_admin),
):
    service = OrderService(db)
    return await service.update(order_id, data)


@router.delete("/{order_id}", status_code=204)
async def delete_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_manager_or_admin),
):
    service = OrderService(db)
    await service.delete(order_id)