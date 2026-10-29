from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.car_repo import CarRepository
from app.models.car import Car
from app.schemas.car import CarCreate, CarUpdate, CarDetailResponse, CarOrderShort


class CarService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CarRepository(session)

    async def list(self, page: int, page_size: int, search: str = None, client_id: int = None):
        return await self.repo.get_all(page, page_size, search, client_id)

    async def get_by_id(self, car_id: int):
        car = await self.repo.get_by_id(car_id)
        if not car:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автомобиль не найден")
        return car

    async def create(self, data: CarCreate):
        # Пункт 6: проверка дубликата госномера
        existing = await self.session.execute(
            select(Car).where(Car.plate == data.plate)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Автомобиль с таким госномером уже существует")
        return await self.repo.create(**data.model_dump(exclude_none=True))

    async def update(self, car_id: int, data: CarUpdate):
        car = await self.repo.get_by_id(car_id)
        if not car:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автомобиль не найден")
        return await self.repo.update(car, **data.model_dump(exclude_unset=True, exclude_none=True))

    async def delete(self, car_id: int):
        car = await self.repo.get_by_id(car_id)
        if not car:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автомобиль не найден")
        await self.repo.delete(car_id)

    async def get_detail(self, car_id: int) -> CarDetailResponse:
        data = await self.repo.get_with_orders(car_id)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Автомобиль не найден")
        
        car = data["car"]
        orders = [
            CarOrderShort(
                id=o.id,
                order_number=o.order_number,
                status=o.status,
                works_description=o.works_description,
                amount=float(o.amount or 0),
                created_at=o.created_at,
            )
            for o in data["orders"]
        ]
        
        return CarDetailResponse(
            id=car.id,
            client_id=car.client_id,
            client_fio=data["client"].fio if data["client"] else "Неизвестно",
            brand=car.brand,
            model=car.model,
            plate=car.plate,
            vin=car.vin,
            year=car.year,
            notes=car.notes,
            created_at=car.created_at,
            orders=orders,
            total_orders=data["total_orders"],
            total_amount=data["total_amount"],
        )