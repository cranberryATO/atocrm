from fastapi import APIRouter
from typing import Annotated
from fastapi import Depends, status, HTTPException

from app.modules.parties.router import router as parties_router
from app.core.dependencies import SessionDep


from sqlmodel import Field, SQLModel, select


class OrganizationCreate(SQLModel):
    name: str = Field(index=True)


class Organization(OrganizationCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)


class OrganizationUpdate(SQLModel):
    name: str | None = None


# TODO : list orgs available for authenticated user
# if org in list, return Organization
def get_org(org_id: int, session: SessionDep) -> int:
    if org_id != 0:
        # 403 if company is not allowed for this user
        # before checking if it exists : do not reveal
        # what companies are in the database
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    return org_id


router = APIRouter(prefix="/orgs")


# TODO : filter by authenticated user orgs -- not from
# org table
@router.get("/")
async def list_organizations(session: SessionDep):
    return list(session.exec(select(Organization)).all())


# CompanyDep = Annotated[str, Depends(get_company)]

router.include_router(
    parties_router,
    prefix="/companies/{company_slug}/parties",
    dependencies=[Depends(get_org)],
)
