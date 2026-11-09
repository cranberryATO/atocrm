from fastapi import status
from fastapi.testclient import TestClient

from app.test.testutils import init_users


def test_no_orgs_at_startup(client: TestClient):
    users = init_users(client, "roger", "paul")

    response = client.get("/orgs/", headers=users["admin"])
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0


def test_user_creates_org(client: TestClient):
    users = init_users(client, "roger", "paul")

    response = client.post(
        "/orgs/", headers=users["roger"], json={"name": "rogers_org"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 1, "name": "rogers_org"}

    # now roger sees one org
    response = client.get("/orgs/", headers=users["roger"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{"id": 1, "name": "rogers_org"}]

    # admin sees one org
    response = client.get("/orgs/", headers=users["admin"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{"id": 1, "name": "rogers_org"}]

    # paul sees no org
    response = client.get("/orgs/", headers=users["paul"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
