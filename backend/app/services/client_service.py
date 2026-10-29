from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.client_repo import ClientRepository
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate, ClientDetailResponse, ClientCarShort, ClientOrderShort


class ClientService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ClientRepository(session)

    async def list(self, page: int, page_size: int, search: str = None):
        return await self.repo.get_all(page, page_size, search)

    async def get_by_id(self, client_id: int):
        client = await self.repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клиент не найден")
        return client

    async def create(self, data: ClientCreate):
        # Пункт 6: проверка дубликата email
        if data.email:
            existing = await self.session.execute(
                select(Client).where(Client.email == data.email)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Клиент с таким email уже существует")
        return await self.repo.create(**data.model_dump(exclude_none=True))

    async def update(self, client_id: int, data: ClientUpdate):
        client = await self.repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клиент не найден")
        return await self.repo.update(client, **data.model_dump(exclude_unset=True, exclude_none=True))

    async def delete(self, client_id: int):
        client = await self.repo.get_by_id(client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клиент не найден")
        await self.repo.delete(client_id)

    async def get_detail(self, client_id: int) -> ClientDetailResponse:
        data = await self.repo.get_with_history(client_id)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клиент не найден")
        
        client = data["client"]
        cars = [ClientCarShort.model_validate(c) for c in data["cars"]]
        orders = [
            ClientOrderShort(
                id=o["order"].id,
                order_number=o["order"].order_number,
                car_plate=o["plate"],
                status=o["order"].status,
                amount=float(o["order"].amount or 0),
                created_at=o["order"].created_at,
            )
            for o in data["orders"]
        ]
        
        return ClientDetailResponse(
            id=client.id,
            fio=client.fio,
            phone=client.phone,
            email=client.email,
            notes=client.notes,
            created_at=client.created_at,
            updated_at=client.updated_at,
            cars=cars,
            orders=orders,
            total_orders=data["total_orders"],
            total_amount=data["total_amount"],
        )