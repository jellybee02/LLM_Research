"""
FastAPI Dependencies
의존성 주입 관리
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from functools import lru_cache

from app.config import get_settings, Settings
from app.services import (
    LLMService,
    QdrantService,
    RouterService,
    ScoringService,
    QAService,
    RAGService,
)
from app.repositories import QARepository, AuditRepository

# 전역 설정
settings = get_settings()

# 데이터베이스 엔진 생성
engine = create_async_engine(
    settings.database.url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    echo=settings.database.echo,
)

# 세션 메이커
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    데이터베이스 세션 의존성
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@lru_cache()
def get_llm_service() -> LLMService:
    """LLM 서비스 의존성"""
    return LLMService(settings)


@lru_cache()
def get_qdrant_service() -> QdrantService:
    """Qdrant 서비스 의존성"""
    return QdrantService(settings)


@lru_cache()
def get_router_service() -> RouterService:
    """라우터 서비스 의존성"""
    llm_service = get_llm_service()
    return RouterService(settings, llm_service)


@lru_cache()
def get_scoring_service() -> ScoringService:
    """채점 서비스 의존성"""
    return ScoringService(settings)


def get_qa_repository(session: AsyncSession) -> QARepository:
    """QA 레포지토리 의존성"""
    return QARepository(session)


def get_audit_repository(session: AsyncSession) -> AuditRepository:
    """감사 레포지토리 의존성"""
    return AuditRepository(session)


def get_qa_service(
    session: AsyncSession,
    llm_service: LLMService,
    scoring_service: ScoringService,
) -> QAService:
    """QA 서비스 의존성"""
    qa_repository = get_qa_repository(session)
    return QAService(settings, llm_service, scoring_service, qa_repository)


def get_rag_service(
    session: AsyncSession,
    llm_service: LLMService,
    qdrant_service: QdrantService,
    router_service: RouterService,
) -> RAGService:
    """RAG 서비스 의존성"""
    audit_repository = get_audit_repository(session)
    return RAGService(
        settings,
        llm_service,
        qdrant_service,
        router_service,
        audit_repository,
    )
