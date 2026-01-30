"""
RAG Service Tests
"""

import pytest
from unittest.mock import Mock, AsyncMock

from app.services import RAGService, LLMService, QdrantService, RouterService
from app.repositories import AuditRepository
from app.config import get_settings
from app.models import DepartmentCode


@pytest.fixture
def settings():
    """설정 픽스처"""
    return get_settings()


@pytest.fixture
def mock_llm_service():
    """LLM 서비스 모의 객체"""
    service = Mock(spec=LLMService)
    service.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    service.generate_completion = AsyncMock(return_value={
        "content": "급성 흉통은 심근경색의 주요 증상입니다. 즉시 응급실을 방문하세요.",
        "model": "gpt-4",
        "tokens": 100,
        "latency_ms": 2000,
    })
    return service


@pytest.fixture
def mock_qdrant_service():
    """Qdrant 서비스 모의 객체"""
    service = Mock(spec=QdrantService)
    service.search_with_fallback = AsyncMock(return_value=[
        {
            "doc_id": "doc_001",
            "title": "급성 관상동맥 증후군",
            "content": "급성 심근경색의 주요 증상은 흉통입니다.",
            "score": 0.92,
            "source": "대한심장학회",
            "metadata": {},
        }
    ])
    return service


@pytest.fixture
def mock_router_service():
    """라우터 서비스 모의 객체"""
    service = Mock(spec=RouterService)
    service.route_question = AsyncMock(return_value=DepartmentCode.EM)
    return service


@pytest.fixture
def mock_audit_repository():
    """감사 레포지토리 모의 객체"""
    repository = Mock(spec=AuditRepository)
    repository.create_rag_log = AsyncMock(return_value=Mock(id=1))
    return repository


@pytest.mark.asyncio
async def test_answer_with_rag(
    settings,
    mock_llm_service,
    mock_qdrant_service,
    mock_router_service,
    mock_audit_repository,
):
    """
    RAG 기반 답변 생성 테스트
    """
    # RAG 서비스 생성
    rag_service = RAGService(
        settings=settings,
        llm_service=mock_llm_service,
        qdrant_service=mock_qdrant_service,
        router_service=mock_router_service,
        audit_repository=mock_audit_repository,
    )
    
    # 답변 생성
    result = await rag_service.answer_with_rag(
        question="급성 흉통이 있을 때 어떻게 해야 하나요?"
    )
    
    # 검증
    assert result["department"] == DepartmentCode.EM.value
    assert "급성" in result["answer"] or "흉통" in result["answer"]
    assert len(result["references"]) > 0
    assert result["references"][0]["doc_id"] == "doc_001"
    assert "meta" in result
    
    # 모의 객체 호출 확인
    mock_router_service.route_question.assert_called_once()
    mock_llm_service.generate_embedding.assert_called_once()
    mock_qdrant_service.search_with_fallback.assert_called_once()
    mock_audit_repository.create_rag_log.assert_called_once()


@pytest.mark.asyncio
async def test_answer_with_manual_department(
    settings,
    mock_llm_service,
    mock_qdrant_service,
    mock_router_service,
    mock_audit_repository,
):
    """
    수동으로 진료과를 지정한 경우 테스트
    """
    rag_service = RAGService(
        settings=settings,
        llm_service=mock_llm_service,
        qdrant_service=mock_qdrant_service,
        router_service=mock_router_service,
        audit_repository=mock_audit_repository,
    )
    
    # 진료과를 직접 지정
    result = await rag_service.answer_with_rag(
        question="당뇨병 관리는 어떻게 하나요?",
        department=DepartmentCode.IM,
    )
    
    # 검증
    assert result["department"] == DepartmentCode.IM.value
    
    # 라우터가 호출되지 않았는지 확인
    mock_router_service.route_question.assert_not_called()


@pytest.mark.asyncio
async def test_answer_with_no_documents(
    settings,
    mock_llm_service,
    mock_router_service,
    mock_audit_repository,
):
    """
    검색된 문서가 없는 경우 테스트
    """
    # 빈 검색 결과 반환하도록 설정
    mock_qdrant = Mock(spec=QdrantService)
    mock_qdrant.search_with_fallback = AsyncMock(return_value=[])
    
    rag_service = RAGService(
        settings=settings,
        llm_service=mock_llm_service,
        qdrant_service=mock_qdrant,
        router_service=mock_router_service,
        audit_repository=mock_audit_repository,
    )
    
    # 답변 생성
    result = await rag_service.answer_with_rag(
        question="알 수 없는 질문"
    )
    
    # 검증
    assert len(result["references"]) == 0
    assert len(result["warnings"]) > 0
    assert "관련 문서" in result["warnings"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
