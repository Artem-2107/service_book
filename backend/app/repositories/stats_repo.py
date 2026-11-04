from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.models.client import Client
from app.models.car import Car
from app.models.order import Order


class StatsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_stats(self) -> dict:
        total_clients = (await self.session.execute(select(func.count(Client.id)))).scalar() or 0
        total_cars = (await self.session.execute(select(func.count(Car.id)))).scalar() or 0
        total_orders = (await self.session.execute(select(func.count(Order.id)))).scalar() or 0
        
        revenue_result = await self.session.execute(
            select(func.coalesce(func.sum(Order.amount), 0))
        )
        total_revenue = float(revenue_result.scalar() or 0)
        
        # Заказы по статусам
        status_result = await self.session.execute(
            select(Order.status, func.count(Order.id))
            .group_by(Order.status)
        )
        orders_by_status = {row[0]: row[1] for row in status_result.all()}
        
        # Заказы за последние 30 дней
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_result = await self.session.execute(
            select(func.count(Order.id)).where(Order.created_at >= thirty_days_ago)
        )
        recent_orders = recent_result.scalar() or 0
        
        return {
            "total_clients": total_clients,
            "total_cars": total_cars,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "orders_by_status": orders_by_status,
            "recent_orders_count": recent_orders,
        }