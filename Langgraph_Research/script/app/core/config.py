from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "QA & Problem Solver API"
    LOG_PATH: str = "log/app.log"   # 프로젝트 루트 기준
    API_PREFIX: str = "/api/v1"

settings = Settings()