from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    project_name: str = "Ai Assistant Web"
    api_prefix: str = "/api/v1"
    secret_key: str = Field(default="change-me-before-production", min_length=16)
    access_token_expire_minutes: int = 60 * 24
    database_url: str = f"sqlite:///{BASE_DIR / 'storage' / 'app.db'}"
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


settings = Settings()
