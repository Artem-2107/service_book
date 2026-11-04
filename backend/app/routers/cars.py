from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import require_manager_or_admin, require_any_authenticated
from app.services.car_service import CarService
from app.schemas.car import CarCreate, CarUpdate, CarResponse, CarDetailResponse, PaginatedCars


router = APIRouter(prefix="/cars", tags=["cars"])


@router.get("/", response_model=PaginatedCars)
async def list_cars(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    client_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_any_authenticated),
):
    service = CarService(db)
    return await service.list(page, page_size, search, client_id)


@router.get("/{car_id}", response_model=CarDetailResponse)
async def get_car_detail(
    car_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_any_authenticated),
):
    """Полная информация об авто с историей заказов."""
    service = CarService(db)
    return await service.get_detail(car_id)


@router.post("/", response_model=CarResponse, status_code=201)
async def create_car(
    data: CarCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_manager_or_admin),
):
    service = CarService(db)
    return await service.create(data)


@router.patch("/{car_id}", response_model=CarResponse)
async def update_car(
    car_id: int,
    data: CarUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_manager_or_admin),
):
    service = CarService(db)
    return await service.update(car_id, data)


@router.delete("/{car_id}", status_code=204)
async def delete_car(
    car_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_manager_or_admin),
):
    service = CarService(db)
    await service.delete(car_id)