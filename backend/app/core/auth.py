from datetime import datetime, timezone, timedelta
import jwt

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, ValidationError
from app.core.users_db import (
    authenticate_user,
    User,
    UserOut,
)
from app.core.database import SessionDep

from app.core.settings import get_settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

AuthDep = Annotated[str, Depends(oauth2_scheme)]


router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    sub: str
    exp: datetime
    # scopes: frozenset[str]


def create_access_token(user: User) -> str:
    assert user.id is not None
    payload = TokenPayload(
        sub=str(user.id),
        exp=datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return jwt.encode(
        payload.model_dump(),
        get_settings().AUTH_SECRET.get_secret_value(),
        algorithm=ALGORITHM,
    )


def decode_token(token: str) -> TokenPayload:
    try:
        raw = jwt.decode(
            token,
            get_settings().AUTH_SECRET.get_secret_value(),
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return TokenPayload.model_validate(raw)
    except jwt.InvalidTokenError, ValidationError:
        raise credentials_exception


@router.post("/token")
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
) -> Token:
    user = authenticate_user(form_data.username, form_data.password, session)
    access_token = create_access_token(user)
    return Token(access_token=access_token, token_type="bearer")


def get_request_token(token: AuthDep) -> TokenPayload:
    return decode_token(token)


TokenDep = Annotated[TokenPayload, Depends(get_request_token)]


def get_current_user(token: TokenDep, session: SessionDep) -> User:
    user = session.get(User, int(token.sub))
    if user is None:
        raise credentials_exception
    return user


UserDep = Annotated[User, Depends(get_current_user)]


def require_admin(user: UserDep):
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN)


@router.get("/me", response_model=UserOut)
def read_users_me(current_user: UserDep):
    return current_user
