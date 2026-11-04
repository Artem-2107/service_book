from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.order_repo import OrderRepository
from app.schemas.order import OrderCreate, OrderUpdate, OrderDetailResponse


class OrderService:
    def __init__(self, session: AsyncSession):
        self.repo = OrderRepository(session)

    async def list(self, page: int, page_size: int, status: str = None, car_id: int = None):
        return await self.repo.get_all(page, page_size, status, car_id)

    async def get_by_id(self, order_id: int):
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
        return order

    async def create(self, data: OrderCreate):
        return await self.repo.create(**data.model_dump(exclude_none=True))

    async def update(self, order_id: int, data: OrderUpdate):
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
        return await self.repo.update(order, **data.model_dump(exclude_unset=True, exclude_none=True))

    async def delete(self, order_id: int):
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
        await self.repo.delete(order_id)

    async def get_detail(self, order_id: int) -> OrderDetailResponse:
        data = await self.repo.get_with_details(order_id)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
        
        order = data["order"]
        car = data["car"]
        client = data["client"]
        
        return OrderDetailResponse(
            id=order.id,
            order_number=order.order_number,
            car_id=car.id,
            car_brand=car.brand,
            car_model=car.model,
            car_plate=car.plate,
            client_id=client.id,
            client_fio=client.fio,
            status=order.status,
            works_description=order.works_description,
            amount=float(order.amount or 0),
            created_at=order.created_at,
            updated_at=order.updated_at,
            completed_at=order.completed_at,
        )