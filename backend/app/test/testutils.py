from fastapi import status
from fastapi.testclient import TestClient


def login(username: str, password: str, _client: TestClient):
    response = _client.post("/token", data={"username": username, "password": password})
    if response.is_success:
        token = response.json().get("access_token")
        auth = {"Authorization": f"Bearer {token}"}
    else:
        auth = {}
    return response, auth


def init_users(_client: TestClient, *usernames: str):
    users: dict[str, dict[str, str]] = {}

    # log in as admin
    response, admin_headers = login("admin", "admin", _client)
    assert response.status_code == status.HTTP_200_OK

    users["admin"] = admin_headers

    # create users
    for i, username in enumerate(usernames):
        password = username + "password"
        response = _client.post(
            "/users/",
            headers=admin_headers,
            json={"username": username, "password": password},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {"id": i + 2, "username": username}
        assert response.headers.get("Location") == f"/users/{i+2}"

        # log in
        response, headers = login(username, password, _client)
        assert response.status_code == status.HTTP_200_OK

        users[username] = headers

    return users
