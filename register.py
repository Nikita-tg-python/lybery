from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

reg = APIRouter(tags=["Register"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypasword")


class Setting(BaseSettings):
    key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env")


setting = Setting()  # type: ignore

fake_users_db = {
    "nikita": {
        "username": "nikita",
        "full_name": "Kriviy Nikita",
        "email": "nikitakryvyj@gmail.com",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$B0+rspDL/i1qXW1SOHEGIg$OvgLEBxeXQSqG8SPvbzppxtoyNneqx8l94nE6cEfkKE",
        "librarian": True,
        "superuser": True,
    },
}


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None


class UserUpdate(User):
    username: str | None = None


class UserInDB(User):
    hashed_password: str


class Librarian(User):
    username: str | None = None
    librarian: bool | None = None


class SuperUser(UserInDB):
    librarian: bool | None = None
    superuser: bool | None = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


def hash_password(password: str):
    return password_hash.hash(password)


def verify_password(password, hashed_password):
    return password_hash.verify(password, hashed_password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return SuperUser(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=setting.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    encoder_jwt = jwt.encode(to_encode, setting.key, algorithm=setting.algorithm)
    return encoder_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    creditials_exeption = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, setting.key, algorithms=[setting.algorithm])
        username = payload.get("sub")
        if username is None:
            raise creditials_exeption
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise creditials_exeption
    if not token_data.username:
        raise HTTPException(status_code=403, detail="User is not found")
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise creditials_exeption
    return user


@reg.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user_dict:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=setting.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user_dict.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@reg.post("/register")
def register(username: str, user_password: str):
    if username in fake_users_db:
        raise HTTPException(status_code=409, detail="User already exists")
    if len(user_password) < 6:
        raise HTTPException(status_code=400, detail="Password is too short")
    hashed_password = hash_password(user_password)
    user = {
        "username": username,
        "full_name": None,
        "email": None,
        "hashed_password": hashed_password,
        "librarian": False,
        "superuser": False,
    }
    fake_users_db[username] = user
    return_user = User(**user)
    return return_user


@reg.patch("/users/{user_name}")
def user_rename(
    user_name: str,
    user: UserUpdate,
    user_db: Annotated[Librarian, Depends(get_current_user)],
) -> User:
    if not user_db.librarian:
        raise HTTPException(status_code=403, detail="Permission denied")
    if user_name not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not in db")
    get_user = fake_users_db[user_name]
    current_user = UserUpdate(**get_user)
    update_user = user.model_dump(exclude_unset=True)
    update_item = current_user.model_copy(update=update_user)
    fake_users_db[user_name] = jsonable_encoder(update_item)
    return update_item


@reg.patch("/admin/librarians/{user_name}")
def librarians(
    user_name: str,
    user: Librarian,
    user_db: Annotated[SuperUser, Depends(get_current_user)],
) -> User:
    if not user_db.superuser:
        raise HTTPException(status_code=403, detail="Permission denied")
    if user_name not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not in db")
    get_user = fake_users_db[user_name]
    current_user = Librarian(**get_user)
    update_user = user.model_dump(exclude_unset=True)
    update_item = current_user.model_copy(update=update_user)
    fake_users_db[user_name] = jsonable_encoder(update_item)
    return update_item


@reg.patch("/user/password/{user_name}")
def password(
    user_name: str,
    user_password: Annotated[str, Body(..., embed=True)],
    user_db: Annotated[SuperUser, Depends(get_current_user)],
) -> User:
    if user_db.username != user_name:
        raise HTTPException(
            status_code=403, detail="You can't change password other user"
        )
    if user_name not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not in db")
    get_user = fake_users_db[user_name]
    update_user_password = hash_password(password=user_password)
    get_user["hashed_password"] = update_user_password
    fake_users_db[user_name] = get_user
    update_user = User(**get_user)
    return update_user


@reg.get("/get/user")
def get_login_user(user: Annotated[UserInDB, Depends(get_current_user)]):
    return user
