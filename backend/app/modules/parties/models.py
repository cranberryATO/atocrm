from sqlmodel import Field, SQLModel


class PartyCreate(SQLModel):
    firstname: str = Field(index=True)
    lastname: str = Field(index=True)


class Party(PartyCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)


class PartyUpdate(SQLModel):
    firstname: str | None = None
    lastname: str | None = None
