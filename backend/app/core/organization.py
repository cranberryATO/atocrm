from fastapi import APIRouter
from typing import Annotated
from fastapi import Depends, status, HTTPException

from app.modules.parties.router import router as parties_router
from app.core.database import SessionDep


from sqlmodel import Field, Relationship, SQLModel, select

from app.core.auth import UserDep
from app.core.users_db import OrganizationUserLink, User


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


# CompanyDep = Annotated[str, Depends(get_company)]

router.include_router(
    parties_router,
    prefix="/orgs/{company_slug}/parties",
)
