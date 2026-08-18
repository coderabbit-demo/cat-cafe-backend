from fastapi import Header, HTTPException, Request, status

from app.core.config import get_settings
from app.schemas.domain import UserRead
from app.services.store import store


def require_service_token(authorization: str | None = Header(default=None)) -> None:
    expected = f"Bearer {get_settings().service_api_token}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid service token"
        )


def require_current_user(request: Request) -> UserRead:
    token = request.cookies.get(get_settings().session_cookie_name)
    user = store.get_session_user(token) if token else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user
