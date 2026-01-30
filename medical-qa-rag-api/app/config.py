"""
Configuration Management
config.yaml 파일을 로드하고 환경변수 오버라이드 지원
"""

import os
from typing import Any, Dict, List, Optional
from pathlib import Path
import yaml
from pydantic import BaseModel, Field
from functools import lru_cache


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False
    cors_origins: List[str] = Field(default_factory=list)


class DatabaseConfig(BaseModel):
    host: str
    port: int = 5432
    name: str
    user: str
    password: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False
    
    @property
    def url(self) -> str:
        """PostgreSQL 연결 URL 생성"""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
    
    @property
    def sync_url(self) -> str:
        """동기 PostgreSQL 연결 URL 생성"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class QdrantCollections(BaseModel):
    em: str = "medical_docs_em"
    im: str = "medical_docs_im"
    ped: str = "medical_docs_ped"
    obgyn: str = "medical_docs_obgyn"
    common: str = "medical_docs_common"


class QdrantSearchConfig(BaseModel):
    top_k: int = 5
    score_threshold: float = 0.7


class QdrantConfig(BaseModel):
    url: str
    api_key: Optional[str] = None
    timeout: int = 30
    collections: QdrantCollections
    search: QdrantSearchConfig


class OpenAIConfig(BaseModel):
    api_key: str
    model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    temperature: float = 0.3
    max_tokens: int = 2000
    timeout: int = 60
    max_retries: int = 3
    request_timeout: int = 30


class DepartmentInfo(BaseModel):
    code: str
    name: str
    name_en: str


class PromptConfig(BaseModel):
    version: str = "1.0.0"
    qa_answering: Dict[str, str]
    router: Dict[str, str]
    rag: Dict[str, Dict[str, str]]


class LoggingFileConfig(BaseModel):
    enabled: bool = True
    path: str = "logs/app.log"
    max_bytes: int = 10485760
    backup_count: int = 5


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"
    audit_enabled: bool = True
    pii_masking: bool = True
    file: LoggingFileConfig


class ScoringConfig(BaseModel):
    exact_match_threshold: float = 0.95
    similarity_threshold: float = 0.8
    use_llm_judge: bool = False


class RateLimitConfig(BaseModel):
    enabled: bool = True
    requests_per_minute: int = 60


class SecurityConfig(BaseModel):
    api_key_header: str = "X-API-Key"
    rate_limit: RateLimitConfig
    pii_fields: List[str] = Field(default_factory=list)


class Settings(BaseModel):
    environment: str = "development"
    server: ServerConfig
    database: DatabaseConfig
    qdrant: QdrantConfig
    openai: OpenAIConfig
    departments: List[DepartmentInfo]
    prompts: PromptConfig
    logging: LoggingConfig
    scoring: ScoringConfig
    security: SecurityConfig
    
    class Config:
        arbitrary_types_allowed = True


def load_config(config_path: str = "config.yaml") -> Settings:
    """
    config.yaml 파일을 로드하고 환경변수로 오버라이드
    
    환경변수 우선순위:
    - DATABASE_PASSWORD 환경변수가 있으면 config.yaml의 password 오버라이드
    - OPENAI_API_KEY 환경변수가 있으면 config.yaml의 api_key 오버라이드
    - QDRANT_API_KEY 환경변수가 있으면 config.yaml의 api_key 오버라이드
    """
    # config.yaml 파일 로드
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, "r", encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)
    
    # 환경변수로 민감 정보 오버라이드
    if os.getenv("DATABASE_PASSWORD"):
        config_dict["database"]["password"] = os.getenv("DATABASE_PASSWORD")
    
    if os.getenv("OPENAI_API_KEY"):
        config_dict["openai"]["api_key"] = os.getenv("OPENAI_API_KEY")
    
    if os.getenv("QDRANT_API_KEY"):
        config_dict["qdrant"]["api_key"] = os.getenv("QDRANT_API_KEY")
    
    # Pydantic 모델로 검증
    return Settings(**config_dict)


@lru_cache()
def get_settings() -> Settings:
    """
    싱글톤 패턴으로 설정 반환
    FastAPI dependency injection에서 사용
    """
    return load_config()


# 전역 설정 객체 (필요시 사용)
settings = get_settings()
