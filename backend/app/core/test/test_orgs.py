from datetime import datetime, timedelta, timezone

from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.test.testutils import init_users
from app.core.organization import OrganizationInvite


def test_no_orgs_at_startup(client: TestClient):
    users = init_users(client, "roger", "paul")

    response = client.get("/orgs/", headers=users["admin"])
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0


def test_user_creates_org(client: TestClient):
    users = init_users(client, "roger", "paul")

    # roger creates an org
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


def test_invites(client: TestClient):
    users = init_users(client, "roger", "paul", "anna")

    # roger creates an org
    response = client.post(
        "/orgs/", headers=users["roger"], json={"name": "rogers_org"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 1, "name": "rogers_org"}

    # paul sees no org
    response = client.get("/orgs/", headers=users["paul"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    # paul is not allowed to create an invite for that org
    response = client.post("/orgs/1/invites", headers=users["paul"])
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # roger creates an invite for his org
    response = client.post("/orgs/1/invites", headers=users["roger"])
    assert response.status_code == status.HTTP_200_OK
    invite = response.json()
    assert invite["invite_org"] == 1

    # paul can join the org with the invite code
    response = client.post(f"/orgs/join/{invite["invite_code"]}", headers=users["paul"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 1, "name": "rogers_org"}

    # then paul can see the org
    response = client.get("/orgs/", headers=users["paul"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{"id": 1, "name": "rogers_org"}]

    # anna cannot join the org with the same invite code
    response = client.post(f"/orgs/join/{invite["invite_code"]}", headers=users["anna"])
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # paul is still not allowed to create an invite for that org
    response = client.post("/orgs/1/invites", headers=users["paul"])
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # roger creates another invite for his org
    response = client.post("/orgs/1/invites", headers=users["roger"])
    assert response.status_code == status.HTTP_200_OK
    invite = response.json()
    assert invite["invite_org"] == 1

    # paul cannot join the org with the invite code because he is already a member
    response = client.post(f"/orgs/join/{invite["invite_code"]}", headers=users["paul"])
    assert response.status_code == status.HTTP_409_CONFLICT


def test_expired_invite(client: TestClient, session: Session):
    users = init_users(client, "roger", "paul")
    client.post("/orgs/", headers=users["roger"], json={"name": "rogers_org"})

    session.add(
        OrganizationInvite(
            invite_code="expired",
            invite_org=1,
            expiry_date=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
    )
    session.commit()

    response = client.post("/orgs/join/expired", headers=users["paul"])
    assert response.status_code == status.HTTP_404_NOT_FOUND

    response = client.post("/orgs/cron", headers=users["paul"])
    assert response.status_code == status.HTTP_403_FORBIDDEN

    assert (
        session.exec(
            select(OrganizationInvite).where(
                OrganizationInvite.invite_code == "expired"
            )
        ).first()
        is not None
    )

    response = client.post("/orgs/cron", headers=users["admin"])
    assert response.status_code == status.HTTP_200_OK

    assert (
        session.exec(
            select(OrganizationInvite).where(
                OrganizationInvite.invite_code == "expired"
            )
        ).all()
        == []
    )
