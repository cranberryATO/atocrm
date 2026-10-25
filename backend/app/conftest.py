import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.dependencies import get_session
from app.main import app


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

    # need to override the app dependency that checks the session
    # otherwise it connects to the app database
    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()
