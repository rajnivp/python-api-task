from typing import Optional

from fastapi import Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import settings


async def verify_token(authorization: str = Header(...)) -> None:
    if authorization != f"Bearer {settings.api_key}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
