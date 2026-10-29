from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.dependencies import require_admin
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserResponse, PaginatedUsers


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=PaginatedUsers)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_admin),  # только admin
):
    service = UserService(db)
    return await service.list(page, page_size, search)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_admin),
):
    service = UserService(db)
    return await service.get_by_id(user_id)


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_admin),
):
    service = UserService(db)
    return await service.create(data)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_admin),
):
    service = UserService(db)
    await service.delete(user_id)