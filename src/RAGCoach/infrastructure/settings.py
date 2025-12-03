from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_provider: str = "ollama"

    ollama_url: str = "http://localhost:11434"
    # Qwen 2.5 3B даёт более стабильный русский, можно переопределить через переменную окружения OLLAMA_MODEL.
    ollama_model: str = "qwen2.5:3b"

    llm_temperature: float = 0.2
    llm_max_tokens: int = 800

    class Config:
        env_file = ".env"


settings = Settings()
