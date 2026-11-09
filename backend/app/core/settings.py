from pathlib import Path
from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# works if this file stays in backend/app/core/
# parents[0]=core, [1]=app, [2]=backend, [3]=monorepo_root
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env.dev",
        populate_by_name=True,
    )
    AUTH_SECRET: SecretStr = Field(min_length=32)
    ADMIN_PASSWORD: SecretStr = Field(min_length=5)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]
