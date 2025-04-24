"""
Authentication middleware for the TAO Dividend Sentiment Service.

This module provides authentication functionality using API key validation.
It includes a dependency function that can be used to protect API endpoints
by verifying the presence and validity of an API key in the request header.
"""

from fastapi import Header, HTTPException, status

from app.core.config import settings


async def verify_token(authorization: str = Header(...)) -> None:
    """
    Verify the API key from the Authorization header.
    
    This function checks if the provided Authorization header contains a valid
    API key. If the key is invalid or missing, it raises an HTTP 401 Unauthorized
    exception.
    
    Args:
        authorization (str): The Authorization header value
        
    Raises:
        HTTPException: If the API key is invalid or missing
    """
    if authorization != f"Bearer {settings.api_key}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
