from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, status

from app.schemas import (
    AdvertisementCreate,
    AdvertisementResponse,
    AdvertisementUpdate,
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app import auth, storage, users_storage

app = FastAPI(
    title="Сервис объявлений",
    description="REST API для объявлений купли/продажи",
    version="1.0.0",
)


@app.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    """Авторизация пользователя, выдача токена на 48 часов."""
    user = users_storage.verify_password(
        username=payload.username,
        password=payload.password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )
    token = auth.create_token(user.id)
    return TokenResponse(access_token=token)


@app.post("/user", response_model=UserResponse)
def create_user(user: UserCreate) -> UserResponse:
    """Создание пользователя (доступно без авторизации)."""
    try:
        return users_storage.create(user)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует",
        )


@app.get("/user", response_model=list[UserResponse])
def list_users(
    current_user: UserResponse = Depends(auth.get_current_user),
) -> list[UserResponse]:
    """Получить список всех пользователей (только admin)."""
    if current_user.group != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав",
        )
    return users_storage.list_users()


@app.get("/user/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID) -> UserResponse:
    """Получить пользователя по id (для всех)."""
    user = users_storage.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.patch("/user/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    data: UserUpdate,
    current_user: UserResponse = Depends(auth.get_current_user),
) -> UserResponse:
    """Обновление данных пользователя."""
    if current_user.group != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для обновления пользователя",
        )
    try:
        user = users_storage.update(user_id, data)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует",
        )
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@app.delete("/user/{user_id}", status_code=204)
def delete_user(
    user_id: UUID,
    current_user: UserResponse = Depends(auth.get_current_user),
) -> None:
    """Удаление пользователя."""
    if current_user.group != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления пользователя",
        )
    if not users_storage.delete(user_id):
        raise HTTPException(status_code=404, detail="Пользователь не найден")


@app.post("/advertisement", response_model=AdvertisementResponse)
def create_advertisement(
    ad: AdvertisementCreate,
    current_user: UserResponse = Depends(auth.get_current_user),
) -> AdvertisementResponse:
    """Создание объявления (только авторизованные пользователи)."""
    ad_with_author = AdvertisementCreate(
        title=ad.title,
        description=ad.description,
        price=ad.price,
        author=current_user.username,
    )
    return storage.create(ad_with_author)


@app.get(
    "/advertisement/{advertisement_id}",
    response_model=AdvertisementResponse,
)
def get_advertisement(advertisement_id: UUID) -> AdvertisementResponse:
    """Получение объявления по id."""
    ad = storage.get_by_id(advertisement_id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return ad


@app.patch(
    "/advertisement/{advertisement_id}",
    response_model=AdvertisementResponse,
)
def update_advertisement(
    advertisement_id: UUID,
    data: AdvertisementUpdate,
    current_user: UserResponse = Depends(auth.get_current_user),
) -> AdvertisementResponse:
    """Частичное обновление объявления (PATCH)."""
    ad = storage.get_by_id(advertisement_id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    if current_user.group != "admin" and current_user.username != ad.author:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для обновления объявления",
        )
    updated = storage.update(advertisement_id, data)
    return updated


@app.delete("/advertisement/{advertisement_id}", status_code=204)
def delete_advertisement(
    advertisement_id: UUID,
    current_user: UserResponse = Depends(auth.get_current_user),
) -> None:
    """Удаление объявления."""
    ad = storage.get_by_id(advertisement_id)
    if ad is None:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    if current_user.group != "admin" and current_user.username != ad.author:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления объявления",
        )
    storage.delete(advertisement_id)


@app.get("/advertisement", response_model=list[AdvertisementResponse])
def search_advertisements(
    title: str | None = Query(None, description="Поиск по заголовку"),
    description: str | None = Query(None, description="Поиск по описанию"),
    price_min: float | None = Query(None, ge=0, description="Мин. цена"),
    price_max: float | None = Query(None, ge=0, description="Макс. цена"),
    author: str | None = Query(None, description="Поиск по автору"),
) -> list[AdvertisementResponse]:
    """Поиск объявлений по полям. Все параметры опциональны (query string)."""
    return storage.search(
        title=title,
        description=description,
        price_min=price_min,
        price_max=price_max,
        author=author,
    )
