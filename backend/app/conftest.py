import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.database import get_session
from app.main import app
from app.core.users_db import create_user_in_db


from os import environ

environ["AUTH_SECRET"] = (
    "test-secret-e081f0b2fbf8c820a9f1e2ccbd96a3e4bc77eff3de2e40666cc70fbc881817d9"
)

environ["ADMIN_PASSWORD"] = "admin"


# this fixture provides the "client" parameter for all test functions
@pytest.fixture
def client():
    # this creates the DB in memory
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        create_user_in_db("admin", "admin", session, is_admin=True)

    # need to override the app dependency that checks the session
    # otherwise it connects to the app database
    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()
