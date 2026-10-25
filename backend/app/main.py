from fastapi import FastAPI
from contextlib import asynccontextmanager


from .core.database import create_db_and_tables
from .modules.parties.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(router, prefix="/parties")


@app.get("/")
async def root():
    return {"message": "Hello World"}
