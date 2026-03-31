from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    project_name: str = "Ai Assistant Web"
    api_prefix: str = "/api/v1"
    secret_key: str = Field(default="change-me-before-production", min_length=16)
    access_token_expire_minutes: int = 60 * 24
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ai_assistant"
    postgres_user: str = "ai_user"
    postgres_password: str = "ai_password"
    database_url: str | None = None
    upload_dir: str = str(BASE_DIR / "storage" / "uploads")
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    demo_user_email: str = "demo@aicontrol.dev"
    demo_user_password: str = "Demo123456!"
    llm_provider: str = "openai"
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4.1-mini"
    dashscope_api_key: str | None = None
    qwen_api_key: str | None = None
    qwen_base_url: str = "https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1"
    qwen_model: str = "qwen3.5-plus"
    ark_api_key: str | None = None
    doubao_api_key: str | None = None
    doubao_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    doubao_model: str = "doubao-seed-1-6-251015"
    openai_timeout_seconds: float = 90.0
    default_max_output_tokens: int = 1200

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def populate_database_url(self) -> "Settings":
        if self.database_url:
            return self

        encoded_user = quote_plus(self.postgres_user)
        encoded_password = quote_plus(self.postgres_password)
        self.database_url = (
            f"postgresql+psycopg://{encoded_user}:{encoded_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        return self


settings = Settings()
