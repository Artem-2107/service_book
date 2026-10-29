from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import require_manager_or_admin, require_any_authenticated
from app.services.client_service import ClientService
from app.schemas.client import (
    ClientCreate, ClientUpdate, ClientResponse, ClientDetailResponse, PaginatedClients
)


router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=PaginatedClients)
async def list_clients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_any_authenticated),
):
    service = ClientService(db)
    return await service.list(page, page_size, search)


@router.get("/{client_id}", response_model=ClientDetailResponse)
async def get_client_detail(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_any_authenticated),
):
    """Полная информация о клиенте с историей авто и заказов."""
    service = ClientService(db)
    return await service.get_detail(client_id)


@router.post("/", response_model=ClientResponse, status_code=201)
async def create_client(
    data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_manager_or_admin),
):
    service = ClientService(db)
    return await service.create(data)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_manager_or_admin),
):
    service = ClientService(db)
    return await service.update(client_id, data)


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_manager_or_admin),
):
    service = ClientService(db)
    await service.delete(client_id)