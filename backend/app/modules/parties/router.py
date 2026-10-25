from typing import Annotated

from fastapi import APIRouter, Query, HTTPException, status, Response
from sqlmodel import select

from ...core.dependencies import SessionDep

from .models import Party, PartyUpdate, PartyCreate

router = APIRouter()


@router.get("/")
async def list_parties(
    session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100
) -> list[Party]:
    parties = session.exec(select(Party).offset(offset).limit(limit)).all()
    return list(parties)


@router.get("/{party_id}")
async def read_party(session: SessionDep, party_id: int) -> Party:
    party = session.get(Party, party_id)
    if not party:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return party


@router.delete(("/{party_id}"))
async def delete_party(session: SessionDep, party_id: int):
    party = session.get(Party, party_id)
    if not party:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    session.delete(party)
    session.commit()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_party(
    party_in: PartyCreate, session: SessionDep, response: Response
) -> Party:
    party = Party.model_validate(party_in)
    session.add(party)
    session.commit()
    session.refresh(party)
    response.headers["Location"] = f"/parties/{party.id}"
    return party


@router.patch("/{party_id}")
async def update_party(
    party_in: PartyUpdate, party_id: int, session: SessionDep
) -> Party:
    party = session.get(Party, party_id)
    if not party:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    party_data = party_in.model_dump(exclude_unset=True)
    party.sqlmodel_update(party_data)
    session.add(party)
    session.commit()
    session.refresh(party)
    return party
