from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from .register import reg

app = FastAPI()

book_db = {}
app.include_router(reg)


class Item(BaseModel):
    book: str | None = None
    author: str = "Nikita"
    num_book: int = 1
    lenguage: str = "English"


@app.get("/books")
def books():
    return list(book_db.values())


@app.get("/book/{book_name}")
def one_book(book_name: str) -> Item:
    if book_name not in book_db:
        raise HTTPException(
            status_code=404, detail="Enter name athere book this book not in db"
        )
    return book_db[book_name]


@app.post("/book/add/")
def add_book(item: Item):
    if item.book in book_db:
        raise HTTPException(status_code=404, detail="This book already exists")
    else:
        book_db[item.book] = {
            "book": item.book,
            "author": item.author,
            "num_book": item.num_book,
            "lenguage": item.lenguage,
        }
        return "book add"


@app.delete("/book/{book_name}")
def delete_book(book_name: str):
    if book_name not in book_db:
        raise HTTPException(
            status_code=404, detail="Enter name another book this book not in db"
        )
    book_db.pop(book_name)
    return "Book delete"


@app.patch("/book/{book_name}")
def patch_book(book_name: str, item: Item):
    if book_name not in book_db:
        raise HTTPException(
            status_code=404, detail="Enter name another book this book not in db"
        )
    stored_book = book_db[book_name]
    stored_book_model = Item(**stored_book)
    update_book = item.model_dump(exclude_unset=True)
    updata_item = stored_book_model.model_copy(update=update_book)
    book_db[book_name] = jsonable_encoder(updata_item)
    return updata_item
