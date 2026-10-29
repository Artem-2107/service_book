from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.clients import router as clients_router
from app.routers.cars import router as cars_router
from app.routers.orders import router as orders_router
from app.routers.stats import router as stats_router

__all__ = [
    "auth_router", "users_router", "clients_router",
    "cars_router", "orders_router", "stats_router",
]