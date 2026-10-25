from fastapi import status
from fastapi.testclient import TestClient


def test_a(client: TestClient):
    # check DB is empty
    response = client.get("/parties/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    # check read on non-existing party returns 404
    response = client.get("/parties/10")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # check create party works
    a_in = {"firstname": "Jean", "lastname": "Bon"}
    a_out = a_in | {"id": 1}
    response = client.post("/parties/", json=a_in)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.headers["location"] == "/parties/1"
    assert a_out == response.json()

    # read the created party
    response = client.get("/parties/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == a_out

    # check list is correct
    response = client.get("/parties/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert a_out == response.json()[0]
