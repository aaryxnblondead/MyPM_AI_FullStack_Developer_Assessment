from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    gemini_api_key: str = ""
    llm_model: str = "gemini-2.5-flash"
    embedding_model: str = "gemini-embedding-2"
    embedding_dim: int = 768
    database_url: str = "sqlite:///./data/app.db"
    frontend_origin: str = "http://localhost:3000"
    prompt_version: str = "v1"
    retrieval_k: int = 4
    judge_batch_size: int = 5
    judge_temperature: float = 0.1
    strong_fit_min: float = 75.0
    moderate_fit_min: float = 45.0
    must_have_weight: float = 2.0
    nice_to_have_weight: float = 1.0
    must_have_miss_cap_share: float = 0.5


settings = Settings()
