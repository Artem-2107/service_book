from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.order import Order
from app.models.car import Car
from app.models.client import Client


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, page: int = 1, page_size: int = 20, status: str = None, car_id: int = None):
        query = select(Order)
        count_query = select(func.count(Order.id))
        
        if status:
            query = query.where(Order.status == status)
            count_query = count_query.where(Order.status == status)
        if car_id:
            query = query.where(Order.car_id == car_id)
            count_query = count_query.where(Order.car_id == car_id)
        
        total = (await self.session.execute(count_query)).scalar()
        query = query.order_by(Order.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        items = result.scalars().all()
        pages = max(1, (total + page_size - 1) // page_size)
        
        return {"items": items, "total": total, "page": page, "pages": pages}

    async def get_by_id(self, order_id: int) -> Order:
        result = await self.session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Order:
        order = Order(**kwargs)
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def update(self, order: Order, **kwargs) -> Order:
        for key, value in kwargs.items():
            setattr(order, key, value)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def delete(self, order_id: int):
        order = await self.get_by_id(order_id)
        if order:
            await self.session.delete(order)
            await self.session.flush()

    async def get_with_details(self, order_id: int):
        """Заказ + авто + клиент."""
        result = await self.session.execute(
            select(Order, Car, Client)
            .join(Car, Order.car_id == Car.id)
            .join(Client, Car.client_id == Client.id)
            .where(Order.id == order_id)
        )
        row = result.first()
        if not row:
            return None
        order, car, client = row
        return {
            "order": order,
            "car": car,
            "client": client,
        }