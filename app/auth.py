from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from app.schemas import UserResponse
from app import users_storage

import secrets


TOKEN_TTL_HOURS = 48


_tokens: dict[str, dict] = {}


def create_token(user_id) -> str:
    """Создать токен для пользователя с заданным сроком."""
    token = secrets.token_urlsafe(32)
    _tokens[token] = {
        "user_id": user_id,
        "expires_at": datetime.now(timezone.utc)
        + timedelta(hours=TOKEN_TTL_HOURS),
    }
    return token


def _get_user_by_token(token: str) -> Optional[UserResponse]:
    data = _tokens.get(token)
    if data is None:
        return None
    if data["expires_at"] < datetime.now(timezone.utc):
        del _tokens[token]
        return None
    return users_storage.get_by_id(data["user_id"])


def get_optional_current_user(
    authorization: str | None = Header(default=None),
) -> Optional[UserResponse]:
    """Получить текущего пользователя, если токен передан и валиден."""
    if authorization is None:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный формат заголовка Authorization",
        )
    user = _get_user_by_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или просроченный токен",
        )
    return user


def get_current_user(
    current_user: UserResponse | None = Depends(get_optional_current_user),
) -> UserResponse:
    """Обязательная авторизация: 401, если пользователь не найден."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
        )
    return current_user
