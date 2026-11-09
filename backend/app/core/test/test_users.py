from fastapi import status
from fastapi.testclient import TestClient


from app.test.testutils import login


def test_users(client: TestClient):
    # list all users while not logged in
    response = client.get("/users/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # log in as admin
    response, admin_headers = login("admin", "admin", client)
    assert response.status_code == status.HTTP_200_OK

    # make sure admin is user id 1
    response = client.get("/users/1", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 1, "username": "admin"}

    # list all users
    response = client.get("/users/", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0] == {"id": 1, "username": "admin"}

    # log paul in (not created yet)
    response, _ = login("paul", "paulspassword", client)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Incorrect username or password"}

    # check there is no user #2
    response = client.get("/users/2", headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # create roger
    response = client.post(
        "/users/",
        headers=admin_headers,
        json={"username": "roger", "password": "rogerspassword"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"id": 2, "username": "roger"}
    assert response.headers.get("Location") == "/users/2"

    # check roger was created like expected
    response = client.get("/users/2", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 2, "username": "roger"}

    # log roger in - wrong password
    response, roger_headers = login("roger", "rogerspasswords", client)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Incorrect username or password"}

    # log roger in
    response, roger_headers = login("roger", "rogerspassword", client)
    assert response.status_code == status.HTTP_200_OK

    # list all users : not authorized
    response = client.get("/users/", headers=roger_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # roger can see himself though
    response = client.get("/me", headers=roger_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 2, "username": "roger"}

    # admin /me
    response = client.get("/me", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 1, "username": "admin"}

    # admin check all users
    # list all users
    response = client.get("/users/", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2
    assert response.json()[0] == {"id": 1, "username": "admin"}
    assert response.json()[1] == {"id": 2, "username": "roger"}

    #  change roger's password
    response = client.patch(
        "/users/2",
        headers=admin_headers,
        json={"password": "azertyuiop"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 2, "username": "roger"}

    # log roger in - old password
    response, roger_headers = login("roger", "rogerspassword", client)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Incorrect username or password"}

    # log roger in - new password
    response, roger_headers = login("roger", "azertyuiop", client)
    assert response.status_code == status.HTTP_200_OK

    #  change password of non-existing user
    response = client.patch(
        "/users/3",
        headers=admin_headers,
        json={"password": "azertyuiop"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_cannot_create_another_admin(client: TestClient):
    # log in as admin
    response, admin_headers = login("admin", "admin", client)
    assert response.status_code == status.HTTP_200_OK

    # create admin
    response = client.post(
        "/users/",
        headers=admin_headers,
        json={"username": "admin", "password": "hello"},
    )
    assert response.status_code == status.HTTP_409_CONFLICT
