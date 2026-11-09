from fastapi import FastAPI, Depends

from contextlib import asynccontextmanager


from app.core.database import create_db_and_tables
from app.core.users_db import create_admin
from app.core.auth import oauth2_scheme


from app.core.users_router import router as user_router
from app.core.auth import router as auth_router
from app.modules.parties.router import router as parties_router
from app.core.organization import router as orgs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    create_admin()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(
    parties_router,
    prefix="/companies/{company_slug}/parties",
    dependencies=[Depends(oauth2_scheme)],
)

app.include_router(user_router)
app.include_router(auth_router, tags=["auth"])
app.include_router(orgs_router)


@app.get("/")
async def root():
    return {
        "message": "Hello World",
    }
