# python environment with UV

Install UV

    curl -LsSf https://astral.sh/uv/install.sh | sh

Init project (/backend)

    uv init app --bare

Install FastAPI

    uv add "fastapi[standard]"

Install dependencies

    uv add sqlmodel
    uv add pytest

Test: launch server

    uv run fastapi dev

Test: launch tests

    uv run pytest

Configure agents skills

    uvx library-skills
