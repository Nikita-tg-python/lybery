import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, pool

from app.database import get_session
from app.main import Book, app
from app.register import SuperUser, hash_password

sqlite_url = "sqlite://"
test_engine = create_engine(
    sqlite_url, connect_args={"check_same_thread": False}, poolclass=pool.StaticPool
)


def get_test_session():
    with Session(test_engine) as session:
        yield session


@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        yield session
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture(session):
    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_superuser")
def test_super_user_fixture(session):
    password = "passwordtest"
    hashed_pw = hash_password(password)

    user = SuperUser(
        username="user_test",
        hashed_password=hashed_pw,
        librarian=True,
        superuser=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return user, password


@pytest.fixture(name="authorized_super_client")
def authorized_super_client_fixture(client, test_superuser):
    user, password = test_superuser

    response = client.post(
        "/login", data={"username": user.username, "password": password}
    )

    token = response.json()["access_token"]

    client.headers.update({"Authorization": f"Bearer {token}"})

    return client


@pytest.fixture(name="test_user")
def test_user_fixture(session):
    password = "passwordtest"
    hashed_pw = hash_password(password)

    user = SuperUser(
        username="user_test",
        hashed_password=hashed_pw,
        librarian=False,
        superuser=False,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return user, password


@pytest.fixture(name="authorized_client")
def authorized_client_fixture(client, test_user):
    user, password = test_user

    response = client.post(
        "/login", data={"username": user.username, "password": password}
    )

    token = response.json()["access_token"]

    client.headers.update({"Authorization": f"Bearer {token}"})

    return client


@pytest.fixture(name="book_1")
def book_1():
    return {"book": "Book 1", "author": "Author 1", "language": "EN"}


@pytest.fixture(name="book_2")
def book_2():
    return {"book": "Book 2", "author": "Author 2", "language": "RU"}


@pytest.fixture(name="book_3")
def book_3():
    return {"book": "Book 3", "author": "Author 3", "language": "UK"}


@pytest.fixture(name="books")
def books(book_1, book_2, book_3):
    return [Book(**book_1), Book(**book_2), Book(**book_3)]


@pytest.fixture(name="user")
def user():
    return {"username": "test", "password": "passwordtest"}


@pytest.fixture(name="user_hash")
def user_hash():
    return {"username": "test", "hashed_password": hash_password("passwordtest")}
