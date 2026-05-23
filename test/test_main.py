def test_books(authorized_client, session, books, book_1, book_2):
    session.add_all(books)
    session.commit()
    response = authorized_client.get("/books?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    assert data[0]["book"] == book_1["book"]
    assert data[0]["author"] == book_1["author"]

    assert data[1]["book"] == book_2["book"]
    assert data[1]["author"] == book_2["author"]


def test_books_un_autorized(client, session, books):
    session.add_all(books)
    session.commit()
    response = client.get("/books?limit=2")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_one_book(authorized_client, session, books, book_2):
    session.add_all(books)
    session.commit()
    response = authorized_client.get("/books/2")
    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 2
    assert data["book"] == book_2["book"]
    assert data["author"] == book_2["author"]


def test_bad_one_book(authorized_client, session, books):
    session.add_all(books)
    session.commit()
    response = authorized_client.get("/books/4")
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_one_book_an_autorized(client, session, books):
    session.add_all(books)
    session.commit()
    response = client.get("/books/2")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_add_book(authorized_super_client, book_1):
    response = authorized_super_client.post("/books", json=book_1)
    assert response.status_code == 200
    data = response.json()

    assert data["book"] == book_1["book"]
    assert data["author"] == book_1["author"]
    assert data["language"] == book_1["language"]


def test_add_book_not_librarian(authorized_client, book_1):
    response = authorized_client.post("/books", json=book_1)
    assert response.status_code == 403
    assert response.json() == {"detail": "Permission denied"}


def test_add_book_an_autorized(client, book_1):
    response = client.post("/books", json=book_1)
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_delete_book(authorized_super_client, session, books):
    session.add_all(books)
    session.commit()

    response = authorized_super_client.delete("/books/1")

    assert response.status_code == 200
    assert response.json() == {"Book delete": True}

    response = authorized_super_client.get("/books/1")
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_delete_book_not_librarian(authorized_client, session, books):
    session.add_all(books)
    session.commit()

    response = authorized_client.delete("/books/1")

    assert response.status_code == 403
    assert response.json() == {"detail": "Permission denied"}


def test_delete_book_an_autorized(client, session, books):
    session.add_all(books)
    session.commit()

    response = client.delete("/books/1")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_bad_delete_book(authorized_super_client, session, books):
    session.add_all(books)
    session.commit()

    response = authorized_super_client.delete("/books/4")

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_path_book(authorized_super_client, session, books, book_2):
    session.add_all(books)
    session.commit()

    response = authorized_super_client.patch("/book/1", json=book_2)

    assert response.status_code == 200
    data = response.json()

    assert data["book"] == book_2["book"]
    assert data["author"] == book_2["author"]
    assert data["language"] == book_2["language"]


def test_path_book_not_librarian(authorized_client, session, books, book_2):
    session.add_all(books)
    session.commit()

    response = authorized_client.patch("/book/1", json=book_2)

    assert response.status_code == 403
    assert response.json() == {"detail": "Permission denied"}


def test_path_book_an_autorized(client, session, books, book_2):
    session.add_all(books)
    session.commit()

    response = client.patch("/book/1", json=book_2)

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_bad_path_book(authorized_super_client, session, books, book_2):
    session.add_all(books)
    session.commit()

    response = authorized_super_client.patch("/book/4", json=book_2)

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}
