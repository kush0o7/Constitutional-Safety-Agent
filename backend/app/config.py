from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Constitutional Safety Agent"
    app_env: str = "development"
    log_level: str = "INFO"

    llm_provider: str = Field(default="mock", description="mock|openai_compatible")
    llm_model: str = "gpt-4o-mini"
    llm_api_base: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_timeout_seconds: float = 30.0

    max_message_chars: int = 8000
    cors_allow_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173"
    eval_reports_dir: str = "evals/reports"
    safety_classifier_mode: str = Field(default="heuristic", description="heuristic|trained")
    safety_model_path: str = "models/safety_classifier.joblib"
    safety_harm_threshold: float = 0.62


settings = Settings()
