from pwdlib import PasswordHash

from sqlmodel import Field, SQLModel, Session, select
from fastapi import HTTPException, status

from app.core.database import engine
from app.core.settings import get_settings

ADMIN_USERNAME = "admin"

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return password_hash.verify(plain_password, hashed_password)


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True, min_length=3)


class UserInDb(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    is_admin: bool = Field(default=False)


class UserOut(UserBase):
    id: int


class UserCreate(UserBase):
    password: str = Field(min_length=4)


class UserUpdate(SQLModel):
    password: str = Field(min_length=4)


def create_admin():
    with Session(engine) as session:
        if get_user_from_db(ADMIN_USERNAME, session) is None:
            create_user_in_db(
                ADMIN_USERNAME,
                get_settings().ADMIN_PASSWORD.get_secret_value(),
                session,
                is_admin=True,
            )


def get_user_from_db(username: str, session: Session) -> UserInDb | None:
    return session.exec(select(UserInDb).where(UserInDb.username == username)).first()


def create_user_in_db(username: str, password: str, session: Session, is_admin: bool):
    user_in_db = UserInDb(
        hashed_password=hash_password(password), username=username, is_admin=is_admin
    )
    session.add(user_in_db)
    session.commit()


def authenticate_user(username: str, password: str, session: Session) -> UserInDb:
    user_in_db = get_user_from_db(username, session)

    if user_in_db is None:
        verify_password(password, DUMMY_HASH)  # to prevent against timing attacks
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )
    if not verify_password(password, user_in_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )
    return user_in_db
