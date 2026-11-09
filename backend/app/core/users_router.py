from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.database import SessionDep
from app.core.users_db import (
    User,
    UserOut,
    UserCreate,
    UserUpdate,
    hash_password,
)
from app.core.auth import require_admin

# Note : Users is by default not protected by authentication, because
# the dependency order is Auth -> Users.
router = APIRouter(
    prefix="/users", tags=["users"], dependencies=[Depends(require_admin)]
)


@router.get("/", response_model=list[UserOut])
def list_users(session: SessionDep):
    return list(session.exec(select(User)).all())


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def add_user(session: SessionDep, user_create: UserCreate, response: Response):
    user_in_db = User(
        hashed_password=hash_password(user_create.password),
        username=user_create.username,
    )
    session.add(user_in_db)
    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already exists."
        )
    session.refresh(user_in_db)
    response.headers["Location"] = f"/users/{user_in_db.id}"
    return user_in_db


@router.get("/{user_id}", response_model=UserOut)
def read_user(session: SessionDep, user_id: int):
    user_in_db = session.get(User, user_id)
    if not user_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return user_in_db


@router.patch("/{user_id}", response_model=UserOut)
def modify_user(session: SessionDep, user_id: int, user_patch: UserUpdate):
    user_in_db = session.get(User, user_id)
    if not user_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    user_in_db.hashed_password = hash_password(user_patch.password)
    session.add(user_in_db)
    session.commit()
    session.refresh(user_in_db)
    return user_in_db
