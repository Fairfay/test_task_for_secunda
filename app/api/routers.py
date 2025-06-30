from fastapi import APIRouter, Depends

from app.core.base import get_api_key
from app.api.endpoints.organization import router as organization_router
from app.api.endpoints.building import router as building_router
from app.api.endpoints.activity import router as activity_router
from app.api.endpoints.user import router as user_router

# Глобальная зависимость на статичный API-ключ для всех публичных эндпоинтов
main_router = APIRouter(dependencies=[Depends(get_api_key)])

# Подключение всех основных роутеров
main_router.include_router(user_router)
main_router.include_router(organization_router)
main_router.include_router(building_router)
main_router.include_router(activity_router)
