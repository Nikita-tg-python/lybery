import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

# Импортируем твой app и функцию, которую будем подменять
from .main import app
from .register import get_session

# Создаем тестовую базу данных SQLite чисто в оперативной памяти
# Она создается мгновенно и удаляется после тестов
sqlite_url = "sqlite://"
test_engine = create_engine(
    sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool
)


def get_test_session():
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def client():
    # Создаем таблицы в тестовой БД
    SQLModel.metadata.create_all(test_engine)

    # ПОДМЕНЯЕМ ЗАВИСИМОСТЬ!
    app.dependency_overrides[get_session] = get_test_session

    with TestClient(app) as c:
        yield c

    # Очищаем подмены и удаляем таблицы после теста
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(test_engine)
