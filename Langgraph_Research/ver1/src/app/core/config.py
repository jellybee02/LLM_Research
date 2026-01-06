from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Dual API Server"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # LLM 관련(예: OpenAI/Azure/Ollama 등)
    LLM_PROVIDER: str = "dummy"

    # VectorDB 관련
    VECTORDB_PROVIDER: str = "chroma"
    VECTORDB_PATH: str = "./data/vectordb"

    class Config:
        env_file = ".env"

settings = Settings()
