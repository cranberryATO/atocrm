from fastapi.testclient import TestClient


def login(username: str, password: str, _client: TestClient):
    response = _client.post("/token", data={"username": username, "password": password})
    if response.is_success:
        token = response.json().get("access_token")
        auth = {"Authorization": f"Bearer {token}"}
    else:
        auth = {}
    return response, auth
