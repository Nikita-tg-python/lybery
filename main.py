from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Field, Session, SQLModel, create_engine, select

from .register import reg


class Setting(BaseSettings):
    sql_url: str

    model_config = SettingsConfigDict(env_file=".env")


setting = Setting()  # type: ignore


class BookBase(SQLModel):
    book: str = Field(index=True)
    author: str = Field(default="Nikita", index=True)
    language: str = Field(default="English", index=True)


class Book(BookBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class BookUpdate(SQLModel):
    book: str | None = None
    author: str | None = None
    language: str | None = None


engine = create_engine(setting.sql_url)


def create_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(reg)


@app.get("/books")
def books(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    books = session.exec(select(Book).offset(offset).limit(limit)).all()
    return books


@app.get("/book/{book_id}")
def one_book(book_id: int, session: SessionDep):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(
            status_code=404, detail="Enter name athere book this book not in db"
        )
    return book


@app.post("/book/add/")
def add_book(book: BookBase, session: SessionDep):
    db_book = Book.model_validate(book)
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book


@app.delete("/book/{book_id}")
def delete_book(book_id: int, session: SessionDep):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(
            status_code=404, detail="Enter name another book this book not in db"
        )
    session.delete(book)
    session.commit()
    return {"Book delete": True}


@app.patch("/book/{book_id}")
def patch_book(book_id: int, book: BookUpdate, session: SessionDep):
    book_db = session.get(Book, book_id)
    if not book_db:
        raise HTTPException(
            status_code=404, detail="Enter name another book this book not in db"
        )
    book_data = book.model_dump(exclude_unset=True)
    book_db.sqlmodel_update(book_data)
    session.add(book_db)
    session.commit()
    session.refresh(book_db)
    return book_db
