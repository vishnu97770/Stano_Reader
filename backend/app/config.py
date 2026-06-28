from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]
    debug: bool = True

    # M17 — Local Ollama configuration
    ollama_url: str = "http://localhost:11434/api/generate"
    ollama_model: str = "llama3.2:1b"
    ollama_timeout: float = 3.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
