from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.car import Car
from app.models.order import Order
from app.models.client import Client


class CarRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, page: int = 1, page_size: int = 20, search: str = None, client_id: int = None):
        query = select(Car)
        count_query = select(func.count(Car.id))
        
        if search:
            pattern = f"%{search}%"
            query = query.where(Car.plate.ilike(pattern))
            count_query = count_query.where(Car.plate.ilike(pattern))
        if client_id:
            query = query.where(Car.client_id == client_id)
            count_query = count_query.where(Car.client_id == client_id)
        
        total = (await self.session.execute(count_query)).scalar()
        query = query.order_by(Car.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        items = result.scalars().all()
        pages = max(1, (total + page_size - 1) // page_size)
        
        return {"items": items, "total": total, "page": page, "pages": pages}

    async def get_by_id(self, car_id: int) -> Car:
        result = await self.session.execute(select(Car).where(Car.id == car_id))
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Car:
        car = Car(**kwargs)
        self.session.add(car)
        await self.session.flush()
        await self.session.refresh(car)
        return car

    async def update(self, car: Car, **kwargs) -> Car:
        for key, value in kwargs.items():
            setattr(car, key, value)
        await self.session.flush()
        await self.session.refresh(car)
        return car

    async def delete(self, car_id: int):
        car = await self.get_by_id(car_id)
        if car:
            await self.session.delete(car)
            await self.session.flush()

    async def get_with_orders(self, car_id: int):
        """Авто + клиент + все заказы этого авто."""
        car = await self.get_by_id(car_id)
        if not car:
            return None
        
        client_result = await self.session.execute(
            select(Client).where(Client.id == car.client_id)
        )
        client = client_result.scalar_one_or_none()
        
        orders_result = await self.session.execute(
            select(Order).where(Order.car_id == car_id).order_by(Order.created_at.desc())
        )
        orders = orders_result.scalars().all()
        
        total_amount = sum(float(o.amount or 0) for o in orders)
        
        return {
            "car": car,
            "client": client,
            "orders": orders,
            "total_orders": len(orders),
            "total_amount": total_amount,
        }