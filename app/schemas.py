from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AdvertisementBase(BaseModel):
    """Базовые поля объявления."""

    title: str = Field(..., min_length=1, description="Заголовок")
    description: str = Field(..., description="Описание")
    price: float = Field(..., ge=0, description="Цена")
    author: str = Field(..., min_length=1, description="Автор")


class AdvertisementCreate(AdvertisementBase):
    """Схема для создания объявления."""

    pass


class AdvertisementUpdate(BaseModel):
    """Схема для частичного обновления объявления (PATCH)."""

    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    author: Optional[str] = Field(None, min_length=1)


class AdvertisementResponse(AdvertisementBase):
    """Схема ответа с объявлением."""

    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class UserBase(BaseModel):
    """Базовые поля пользователя."""

    username: str = Field(..., min_length=1, description="Имя пользователя")
    group: Literal["user", "admin"] = Field(
        "user",
        description="Группа пользователя: user или admin",
    )


class UserCreate(UserBase):
    """Схема для создания пользователя."""

    password: str = Field(..., min_length=1, description="Пароль")


class UserUpdate(BaseModel):
    """Схема для частичного обновления пользователя."""

    username: Optional[str] = Field(None, min_length=1)
    password: Optional[str] = Field(None, min_length=1)
    group: Optional[Literal["user", "admin"]] = None


class UserResponse(UserBase):
    """Схема ответа с пользователем (без пароля)."""

    id: UUID
    created_at: datetime


class LoginRequest(BaseModel):
    """Данные для логина."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Токен авторизации."""

    access_token: str
    token_type: str = "bearer"
