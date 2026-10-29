from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import require_any_authenticated
from app.services.stats_service import StatsService
from app.schemas.stats import StatsResponse


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_any_authenticated),
):
    """Статистика по системе."""
    service = StatsService(db)
    return await service.get_stats()