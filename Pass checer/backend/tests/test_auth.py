from tests.helpers import login, register


def test_register_success(client):
    response = register(client)
    assert response.status_code == 201


def test_register_rejects_weak_password(client):
    response = client.post("/api/register", json={"username": "weakuser", "password": "123456"})
    assert response.status_code == 400
    assert "issues" in response.get_json()


def test_register_rejects_duplicate_username(client):
    register(client, username="alice")
    response = register(client, username="alice")
    assert response.status_code == 409


def test_register_rejects_invalid_username(client):
    response = client.post(
        "/api/register", json={"username": "a", "password": "Correct-Horse-42!"}
    )
    assert response.status_code == 400


def test_login_success_sets_session(client):
    register(client, username="alice")
    response = login(client, username="alice")
    assert response.status_code == 200
    assert response.get_json()["username"] == "alice"

    me = client.get("/api/me")
    assert me.status_code == 200
    assert me.get_json()["username"] == "alice"


def test_login_wrong_password_is_generic_and_recorded(client):
    register(client, username="alice")
    response = login(client, username="alice", password="totally-wrong")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid username or password"


def test_login_nonexistent_user_gives_same_generic_error(client):
    response = login(client, username="nobody", password="whatever-Password1!")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid username or password"


def test_logout_clears_session(client):
    register(client, username="alice")
    login(client, username="alice")
    client.post("/api/logout")
    response = client.get("/api/me")
    assert response.status_code == 401


def test_check_password_endpoint_does_not_require_login(client):
    response = client.post("/api/check-password", json={"password": "correct-horse-battery-staple-42"})
    assert response.status_code == 200
    assert "rating" in response.get_json()
