from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashed/secret",
        "librarian": False,
        "superuser": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashed/secret2",
        "librarian": False,
        "superuser": False,
    },
    "nikita": {
        "username": "nikita",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashed/kisame2kisame",
        "librarian": True,
        "superuser": True,
    },
}

reg = APIRouter(tags=["Register"])


def fake_hash_password(password: str):
    return "fakehashed/" + password


def ancoder_hash(password: str):
    return password.split("/")[1]


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None


class UserUpdate(User):
    username: str | None = None


class UserInDB(User):
    hashed_password: str


class Librarian(UserInDB):
    username: str | None = None
    librarian: bool = False


class SuperUser(Librarian):
    superuser: bool = False


def user_data(db, username: str):
    if username in db:
        user_dict = db[username]
        return SuperUser(**user_dict)


def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = user_data(fake_users_db, token)
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@reg.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}


@reg.post("/register")
def register(username: str, user_password: str):
    if username in fake_users_db:
        raise HTTPException(status_code=404, detail="User already exists")
    if len(user_password) < 6:
        raise HTTPException(status_code=404, detail="Password is too short")
    hashed_password = fake_hash_password(user_password)
    user = {"username": username, "hashed_password": hashed_password}
    fake_users_db[username] = user
    return fake_users_db


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
    user_data = fake_users_db[user_name]
    current_user = UserUpdate(**user_data)
    update_user = user.model_dump(exclude_unset=True)
    update_item = current_user.model_copy(update=update_user)
    fake_users_db[user_name] = jsonable_encoder(update_item)
    return update_item


@reg.patch("/admin/liberarians/{user_name}")
def liberarians(
    user_name: str,
    user: Librarian,
    user_db: Annotated[SuperUser, Depends(get_current_user)],
) -> User:
    if not user_db.superuser:
        raise HTTPException(status_code=403, detail="Permission denied")
    if user_name not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not in db")
    user_data = fake_users_db[user_name]
    current_user = Librarian(**user_data)
    update_user = user.model_dump(exclude_unset=True)
    update_item = current_user.model_copy(update=update_user)
    fake_users_db[user_name] = jsonable_encoder(update_item)
    return update_item


@reg.patch("/user/password/{user_name}")
def password(
    user_name: str,
    user: UserInDB,
    user_db: Annotated[UserUpdate, Depends(get_current_user)],
) -> User:
    if not user_db.username == user_name:
        raise HTTPException(
            status_code=403, detail="You can't change password ather user"
        )
    if user_name not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not in db")
    user_data = fake_users_db[user_name]
    current_user = UserInDB(**user_data)
    update_user = user.model_dump(exclude_unset=True)
    update_item = current_user.model_copy(update=update_user)
    fake_users_db[user_name] = jsonable_encoder(update_item)
    return update_item
