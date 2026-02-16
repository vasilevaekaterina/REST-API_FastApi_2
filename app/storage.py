"""Хранилище объявлений в памяти (без БД)."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from app.schemas import (
    AdvertisementCreate,
    AdvertisementUpdate,
    AdvertisementResponse,
)


_advertisements: dict[UUID, dict] = {}


def create(ad: AdvertisementCreate) -> AdvertisementResponse:
    """Создать объявление."""
    ad_id = uuid4()
    now = datetime.now(timezone.utc)
    record = {
        "id": ad_id,
        "title": ad.title,
        "description": ad.description,
        "price": ad.price,
        "author": ad.author,
        "created_at": now,
    }
    _advertisements[ad_id] = record
    return AdvertisementResponse(**record)


def get_by_id(ad_id: UUID) -> Optional[AdvertisementResponse]:
    """Получить объявление по id."""
    record = _advertisements.get(ad_id)
    if record is None:
        return None
    return AdvertisementResponse(**record)


def update(
    ad_id: UUID, data: AdvertisementUpdate
) -> Optional[AdvertisementResponse]:
    """Частично обновить объявление (PATCH)."""
    record = _advertisements.get(ad_id)
    if record is None:
        return None
    update_dict = data.model_dump(exclude_unset=True)
    record.update(update_dict)
    return AdvertisementResponse(**record)


def delete(ad_id: UUID) -> bool:
    """Удалить объявление. Возвращает True, если удалено."""
    if ad_id in _advertisements:
        del _advertisements[ad_id]
        return True
    return False


def search(
    title: Optional[str] = None,
    description: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    author: Optional[str] = None,
) -> list[AdvertisementResponse]:
    """Поиск объявлений по полям (все параметры опциональны)."""
    result = []
    for record in _advertisements.values():
        if title is not None and title.lower() not in record["title"].lower():
            continue
        if description is not None and description.lower() not in record[
            "description"
        ].lower():
            continue
        if price_min is not None and record["price"] < price_min:
            continue
        if price_max is not None and record["price"] > price_max:
            continue
        if author is not None and author.lower() not in record[
            "author"
        ].lower():
            continue
        result.append(AdvertisementResponse(**record))
    result.sort(key=lambda x: x.created_at, reverse=True)
    return result
