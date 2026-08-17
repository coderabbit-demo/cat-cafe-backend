from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from google.auth.exceptions import GoogleAuthError, TransportError

from app.core.config import get_settings
from app.core.google_auth import verify_google_id_token
from app.core.security import require_current_user
from app.schemas.domain import GoogleCredential, UserCreate, UserRead
from app.services.store import store

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate) -> UserRead:
    return UserRead(id=store.create_user(str(payload.email)), email=payload.email)


@router.post("/google", response_model=UserRead)
def google_sign_in(payload: GoogleCredential, response: Response) -> UserRead:
    try:
        claims = verify_google_id_token(payload.credential)
    except TransportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google token verification is unavailable",
        ) from exc
    except (GoogleAuthError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential",
        ) from exc

    user = store.sign_in_with_google(str(claims["sub"]), str(claims["email"]))
    settings = get_settings()
    session_token = store.create_session(user.id, settings.session_ttl_seconds)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    return user


@router.get("/me", response_model=UserRead)
def me(current_user: Annotated[UserRead, Depends(require_current_user)]) -> UserRead:
    return current_user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response) -> None:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        store.delete_session(token)
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
