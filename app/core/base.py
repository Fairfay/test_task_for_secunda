import logging

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import settings


api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def get_api_key(api_key: str = Security(api_key_header)):
    """
    Зависимость для проверки заголовка X-API-KEY для доступа к публичному API.
    Вызывает HTTP 401, если статический ключ отсутствует или недействителен
    """
    if api_key == settings.api_key:
        return api_key
    logging.warning("Неверный или отсутствующий ключ API")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверный или отсутствующий ключ API",
    )
