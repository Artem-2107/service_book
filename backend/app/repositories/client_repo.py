from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.client import Client
from app.models.car import Car
from app.models.order import Order


class ClientRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, page: int = 1, page_size: int = 20, search: str = None):
        query = select(Client)
        count_query = select(func.count(Client.id))
        
        if search:
            pattern = f"%{search}%"
            query = query.where(Client.fio.ilike(pattern))
            count_query = count_query.where(Client.fio.ilike(pattern))
        
        total = (await self.session.execute(count_query)).scalar()
        query = query.order_by(Client.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        items = result.scalars().all()
        pages = max(1, (total + page_size - 1) // page_size)
        
        return {"items": items, "total": total, "page": page, "pages": pages}

    async def get_by_id(self, client_id: int) -> Client:
        result = await self.session.execute(select(Client).where(Client.id == client_id))
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Client:
        client = Client(**kwargs)
        self.session.add(client)
        await self.session.flush()
        await self.session.refresh(client)
        return client

    async def update(self, client: Client, **kwargs) -> Client:
        for key, value in kwargs.items():
            setattr(client, key, value)
        await self.session.flush()
        await self.session.refresh(client)
        return client

    async def delete(self, client_id: int):
        client = await self.get_by_id(client_id)
        if client:
            await self.session.delete(client)
            await self.session.flush()

    async def get_with_history(self, client_id: int):
        """Клиент + все его авто + все заказы по этим авто (JOIN)."""
        client = await self.get_by_id(client_id)
        if not client:
            return None
        
        # Все авто клиента
        cars_result = await self.session.execute(
            select(Car).where(Car.client_id == client_id).order_by(Car.created_at.desc())
        )
        cars = cars_result.scalars().all()
        
        # Все заказы по авто клиента
        car_ids = [c.id for c in cars]
        orders = []
        total_amount = 0.0
        if car_ids:
            orders_result = await self.session.execute(
                select(Order, Car.plate)
                .join(Car, Order.car_id == Car.id)
                .where(Car.client_id == client_id)
                .order_by(Order.created_at.desc())
            )
            for order, plate in orders_result.all():
                orders.append({"order": order, "plate": plate})
                total_amount += float(order.amount or 0)
        
        return {
            "client": client,
            "cars": cars,
            "orders": orders,
            "total_orders": len(orders),
            "total_amount": total_amount,
        }