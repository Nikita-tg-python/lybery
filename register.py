from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Field, Session, SQLModel, create_engine, select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypasword")
# "postgresql://nikita:kisame2kisame@localhost:5432/user_db"
sql_file_name = "user_database.db"
sql_url = f"sqlite:///{sql_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sql_url, connect_args=connect_args)


class Setting(BaseSettings):
    key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env")


setting = Setting()  # type: ignore


class User(SQLModel):
    username: str = Field(unique=True, index=True)
    email: str | None = Field(default=None, index=True)
    full_name: str | None = Field(default=None, index=True)


class UserUpdate(User):
    email: str | None = None
    full_name: str | None = None
    username: str | None = None


class UserInDB(User):
    hashed_password: str


class Librarian(User):
    username: str | None = None
    librarian: bool | None = None


class SuperUser(UserInDB, table=True):
    id: int | None = Field(default=None, primary_key=True)
    librarian: bool | None = None
    superuser: bool | None = None


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: str | None = None


def create_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: APIRouter):
    create_db()
    yield


reg = APIRouter(tags=["Register"], lifespan=lifespan)


def hash_password(password: str):
    return password_hash.hash(password)


def verify_password(password, hashed_password):
    return password_hash.verify(password, hashed_password)


def get_user(username: str, session: Session):
    return session.exec(select(SuperUser).where(SuperUser.username == username)).first()


def authenticate_user(username: str, password: str, session: Session):
    user = get_user(username=username, session=session)
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


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep
):
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
    user = get_user(username=token_data.username, session=session)
    if user is None:
        raise creditials_exeption
    return user


@reg.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
):
    user_dict = authenticate_user(
        username=form_data.username,
        password=form_data.password,
        session=session,
    )
    if not user_dict:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=setting.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user_dict.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@reg.post("/register", response_model=User)
def register(username: str, user_password: str, session: SessionDep):
    user_db = get_user(username=username, session=session)
    if user_db:
        raise HTTPException(status_code=409, detail="User already exists")
    if len(user_password) < 6:
        raise HTTPException(status_code=400, detail="Password is too short")
    hashed_password = hash_password(user_password)
    user = SuperUser(
        username=username,
        full_name=None,
        email=None,
        hashed_password=hashed_password,
        librarian=False,
        superuser=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@reg.patch("/users/{username}")
def user_rename(
    username: str,
    user: UserUpdate,
    user_db: Annotated[Librarian, Depends(get_current_user)],
    session: SessionDep,
) -> User:
    if not user_db.librarian:
        raise HTTPException(status_code=403, detail="Permission denied")
    target_user = get_user(username=username, session=session)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not in db")
    update_user = user.model_dump(exclude_unset=True)
    target_user.sqlmodel_update(update_user)
    session.add(target_user)
    session.commit()
    session.refresh(target_user)
    return target_user


@reg.patch("/admin/librarians/{username}")
def librarians(
    username: str,
    user: Librarian,
    user_db: Annotated[SuperUser, Depends(get_current_user)],
    session: SessionDep,
) -> User:
    if not user_db.superuser:
        raise HTTPException(status_code=403, detail="Permission denied")
    target_user = get_user(username=username, session=session)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not in db")
    update_user = user.model_dump(exclude_unset=True)
    target_user.sqlmodel_update(update_user)
    session.add(target_user)
    session.commit()
    session.refresh(target_user)
    return target_user


@reg.patch("/user/password/{username}")
def password(
    username: str,
    user_password: Annotated[str, Body(..., embed=True)],
    user_db: Annotated[SuperUser, Depends(get_current_user)],
    session: SessionDep,
) -> User:
    if user_db.username != username:
        raise HTTPException(
            status_code=403, detail="You can't change password other user"
        )
    new_hashed_paswword = hash_password(user_password)
    user_db.hashed_password = new_hashed_paswword
    session.add(user_db)
    session.commit()
    session.refresh(user_db)
    return user_db


@reg.get("/get/user")
def get_login_user(user: Annotated[UserInDB, Depends(get_current_user)]):
    return user
