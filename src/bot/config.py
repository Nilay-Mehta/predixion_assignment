from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = "gemini"
    gemini_model: str = "gemini-2.5-flash"
    google_api_key: str | None = None
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    github_models_token: str | None = None
    github_models_model: str = "gpt-4o-mini"
    github_models_base_url: str = "https://models.inference.ai.azure.com"
    tavily_api_key: str | None = None
    github_token: str | None = None
    max_plan_steps: int = 6
    max_llm_calls_per_run: int = 12
    tool_timeout_seconds: float = 10
    search_depth: str = "basic"


settings = Settings()
