from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.stats_repo import StatsRepository


class StatsService:
    def __init__(self, session: AsyncSession):
        self.repo = StatsRepository(session)

    async def get_stats(self):
        return await self.repo.get_stats()