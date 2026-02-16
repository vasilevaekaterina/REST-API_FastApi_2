"""Хранилище пользователей в памяти (без БД)."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from app.schemas import UserCreate, UserUpdate, UserResponse


_users: dict[UUID, dict] = {}


def _to_response(record: dict) -> UserResponse:
    return UserResponse(
        id=record["id"],
        username=record["username"],
        group=record["group"],
        created_at=record["created_at"],
    )


def create(user: UserCreate) -> UserResponse:
    """Создать пользователя. username должен быть уникальным."""
    if any(rec["username"] == user.username for rec in _users.values()):
        raise ValueError("Пользователь с таким именем уже существует")
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    record = {
        "id": user_id,
        "username": user.username,
        "password": user.password,
        "group": user.group,
        "created_at": now,
    }
    _users[user_id] = record
    return _to_response(record)


def get_by_id(user_id: UUID) -> Optional[UserResponse]:
    """Получить пользователя по id."""
    record = _users.get(user_id)
    if record is None:
        return None
    return _to_response(record)


def list_users() -> list[UserResponse]:
    """Получить список всех пользователей."""
    responses = [_to_response(record) for record in _users.values()]
    responses.sort(key=lambda user: user.created_at)
    return responses


def update(user_id: UUID, data: UserUpdate) -> Optional[UserResponse]:
    """Частично обновить пользователя."""
    record = _users.get(user_id)
    if record is None:
        return None
    update_data = data.model_dump(exclude_unset=True)
    new_username = update_data.get("username")
    if new_username and new_username != record["username"]:
        if any(
            rec["username"] == new_username and rec["id"] != user_id
            for rec in _users.values()
        ):
            raise ValueError("Пользователь с таким именем уже существует")
    record.update(update_data)
    return _to_response(record)


def delete(user_id: UUID) -> bool:
    """Удалить пользователя."""
    if user_id in _users:
        del _users[user_id]
        return True
    return False


def verify_password(username: str, password: str) -> Optional[UserResponse]:
    """Проверить логин и пароль, вернуть пользователя при успехе."""
    for record in _users.values():
        if record["username"] == username and record["password"] == password:
            return _to_response(record)
    return None
