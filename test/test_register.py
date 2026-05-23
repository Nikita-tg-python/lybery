from app.register import SuperUser


def test_get_login_user(authorized_super_client, test_superuser):
    user, _ = test_superuser

    response = authorized_super_client.get("/get/user")

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == user.username


def test_login(client, test_user):
    user, password = test_user

    response = client.post(
        "/login",
        data={
            "username": user.username,
            "password": password,
        },
    )
    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    assert len(data["access_token"]) > 0


def test_bad_login(client, user):

    response = client.post("/login", data=user)
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


def test_register(client, user):

    response = client.post("/register", json=user)
    assert response.status_code == 200

    data = response.json()

    assert data["username"] == user["username"]


def test_register_in_db(session, client, user_hash, user):
    session.add(SuperUser(**user_hash))
    session.commit()

    response = client.post("/register", json=user)

    assert response.status_code == 409
    assert response.json() == {"detail": "User already exists"}


def test_register_len(client):

    response = client.post("/register", json={"username": "test", "password": "test"})
    assert response.status_code == 400

    assert response.json() == {"detail": "Password is too short"}


def test_user_rename(authorized_client):
    response = authorized_client.patch("/users/me", json={"username": "nikita"})

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "nikita"


def test_user_rename_an_autorized(client):
    response = client.patch("/users/me", json={"username": "nikita"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_librarians(authorized_super_client, session, user_hash):
    session.add(SuperUser(**user_hash))
    session.commit()

    response = authorized_super_client.patch(
        "/admin/librarians/test", json={"librarian": True}
    )

    assert response.status_code == 200

    data = response.json()

    assert "librarian" in data
    assert data["username"] == user_hash["username"]


def test_librarians_an_superuser(authorized_client, session, user_hash):
    session.add(SuperUser(**user_hash))
    session.commit()

    response = authorized_client.patch(
        "/admin/librarians/test", json={"librarian": True}
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Permission denied"}


def test_librarians_an_autorized(client, session, user_hash):
    session.add(SuperUser(**user_hash))
    session.commit()

    response = client.patch("/admin/librarians/test", json={"librarian": True})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_librarians_username(authorized_super_client, session, user_hash):
    session.add(SuperUser(**user_hash))
    session.commit()

    response = authorized_super_client.patch(
        "/admin/librarians/test2", json={"librarian": True}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User not in db"}


def test_password(authorized_client):
    response = authorized_client.patch(
        "/users/password/me", json={"user_password": "nikita"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "user_test"


def test_password_an_autorized(client):
    response = client.patch("/users/password/me", json={"user_password": "nikita"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
