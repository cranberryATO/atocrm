from typing import Annotated
from datetime import datetime, timedelta, timezone
import uuid

from fastapi import APIRouter, Depends
from fastapi import status, HTTPException


from app.modules.parties.router import router as parties_router
from app.core.database import SessionDep

from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, Relationship, SQLModel, select, delete, col

from app.core.auth import UserDep, require_admin
from app.core.users_db import OrganizationUserLink, User

INVITE_EXPIRY_DAYS = 3


class OrganizationInvite(SQLModel, table=True):
    invite_code: str = Field(primary_key=True)
    invite_org: int = Field(foreign_key="organization.id")
    expiry_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
        + timedelta(days=INVITE_EXPIRY_DAYS)
    )


class OrganizationCreate(SQLModel):
    name: str = Field(index=True)


class Organization(OrganizationCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    members: list[User] = Relationship(
        back_populates="orgs", link_model=OrganizationUserLink
    )


class OrganizationUpdate(SQLModel):
    name: str | None = None


router = APIRouter(prefix="/orgs", tags=["Organization"])


@router.get("/")
def list_organizations(user: UserDep, session: SessionDep):
    if user.is_admin:
        return list(session.exec(select(Organization)).all())
    else:
        return user.orgs


def get_org_admin_link(
    org_id: int, user: UserDep, session: SessionDep
) -> OrganizationUserLink:
    link = session.get(OrganizationUserLink, {"org_id": org_id, "member_id": user.id})
    if link is None or not link.is_org_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    return link


OrgAdminDep = Annotated[OrganizationUserLink, Depends(get_org_admin_link)]


@router.post("/")
def create_organization(user: UserDep, session: SessionDep, org: OrganizationCreate):
    new_org = Organization.model_validate(org)

    session.add(new_org)
    session.flush()
    session.add(
        OrganizationUserLink(org_id=new_org.id, member_id=user.id, is_org_admin=True)
    )
    session.commit()
    session.refresh(new_org)
    return new_org


@router.post("/{org_id}/invites", dependencies=[Depends(get_org_admin_link)])
def create_invite(org_id: int, session: SessionDep):
    new_invite = OrganizationInvite(invite_code=str(uuid.uuid4()), invite_org=org_id)
    session.add(new_invite)
    session.commit()
    session.refresh(new_invite)
    return new_invite


@router.post("/join/{invite_code}")
def accept_invite(invite_code: str, user: UserDep, session: SessionDep):
    invite_org_id = session.exec(
        delete(OrganizationInvite)
        .where(col(OrganizationInvite.invite_code) == invite_code)
        .where(col(OrganizationInvite.expiry_date) > datetime.now(timezone.utc))
        .returning(col(OrganizationInvite.invite_org))
    ).scalar_one_or_none()
    if invite_org_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    session.add(
        OrganizationUserLink(
            org_id=invite_org_id, member_id=user.id, is_org_admin=False
        )
    )

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT)
    return session.get(Organization, invite_org_id)


@router.post("/cron", dependencies=[Depends(require_admin)])
def cron(session: SessionDep):
    # cleanup expired invites
    session.exec(
        delete(OrganizationInvite).where(
            col(OrganizationInvite.expiry_date) < datetime.now(timezone.utc)
        )
    )
    session.commit()


router.include_router(
    parties_router,
    prefix="/{org_id}/parties",
)
