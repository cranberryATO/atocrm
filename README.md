# ATO CRM

# Backend

Launch server (from backend/app)

    uv run fastapi dev

Launch tests (from backend/app)

    uv run pytest

to launch tests only on a module:

    uv run pytest modules/parties/

Coverage tests

    uv run pytest --cov=app --cov-branch --cov-report=term-missing
