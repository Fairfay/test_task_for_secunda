from fastapi import FastAPI

from app.api.routers import main_router
from app.core.config import settings
from app.core.init_db import create_first_superuser, fill_test_data


app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
)
app.include_router(main_router, prefix="/api/v1")


@app.on_event('startup')
async def startup():
    await create_first_superuser()
    await fill_test_data()


@app.get(
    "/health", tags=["Health"],
    summary="Проверка состояния API", response_description="Статус OK"
)
async def health_check():
    """Проверка, что сервис запущен и работает корректно."""
    return {"status": "ok"}
