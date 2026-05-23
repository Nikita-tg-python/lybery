from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, SQLModel, select

from app.database import SessionDep, engine
from app.register import Librarian, User, get_current_user, reg


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


def create_db():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(reg)


@app.get("/books")
def books(
    user: Annotated[User, Depends(get_current_user)],
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    books = session.exec(select(Book).offset(offset).limit(limit)).all()
    return books


@app.get("/books/{book_id}")
def one_book(
    book_id: int, user: Annotated[User, Depends(get_current_user)], session: SessionDep
):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.post("/books")
def add_book(
    book: BookBase,
    librarian: Annotated[Librarian, Depends(get_current_user)],
    session: SessionDep,
):
    if not librarian.librarian:
        raise HTTPException(status_code=403, detail="Permission denied")
    db_book = Book.model_validate(book)
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book


@app.delete("/books/{book_id}")
def delete_book(
    book_id: int,
    librarian: Annotated[Librarian, Depends(get_current_user)],
    session: SessionDep,
):
    if not librarian.librarian:
        raise HTTPException(status_code=403, detail="Permission denied")
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    session.delete(book)
    session.commit()
    return {"Book delete": True}


@app.patch("/book/{book_id}")
def patch_book(
    book_id: int,
    book: BookUpdate,
    librarian: Annotated[Librarian, Depends(get_current_user)],
    session: SessionDep,
):
    if not librarian.librarian:
        raise HTTPException(status_code=403, detail="Permission denied")
    book_db = session.get(Book, book_id)
    if not book_db:
        raise HTTPException(status_code=404, detail="Book not found")
    book_data = book.model_dump(exclude_unset=True)
    book_db.sqlmodel_update(book_data)
    session.add(book_db)
    session.commit()
    session.refresh(book_db)
    return book_db
