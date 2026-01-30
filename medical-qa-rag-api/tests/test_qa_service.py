"""
QA Service Tests
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.services import QAService, LLMService, ScoringService
from app.repositories import QARepository
from app.config import get_settings


@pytest.fixture
def settings():
    """설정 픽스처"""
    return get_settings()


@pytest.fixture
def mock_llm_service():
    """LLM 서비스 모의 객체"""
    service = Mock(spec=LLMService)
    service.generate_completion = AsyncMock(return_value={
        "content": "2",
        "model": "gpt-4",
        "tokens": 50,
        "latency_ms": 1000,
    })
    return service


@pytest.fixture
def mock_scoring_service():
    """채점 서비스 모의 객체"""
    service = Mock(spec=ScoringService)
    service.score_answer = Mock(return_value={
        "is_correct": True,
        "score": 1.0,
        "explanation": "정답",
    })
    return service


@pytest.fixture
def mock_qa_repository():
    """QA 레포지토리 모의 객체"""
    repository = Mock(spec=QARepository)
    repository.get_qa_by_id = AsyncMock(return_value=Mock(
        id=1,
        question="급성 심근경색의 주요 증상은?\n1. 두통\n2. 흉통\n3. 복통",
        answer="2",
        q_type="multiple_choice",
        domain="응급의학",
        choices=["두통", "흉통", "복통"],
    ))
    repository.create_attempt_log = AsyncMock(return_value=Mock(id=1))
    return repository


@pytest.mark.asyncio
async def test_answer_question_with_qa_id(
    settings,
    mock_llm_service,
    mock_scoring_service,
    mock_qa_repository,
):
    """
    qa_id로 문제를 조회하고 답변 생성 테스트
    """
    # QA 서비스 생성
    qa_service = QAService(
        settings=settings,
        llm_service=mock_llm_service,
        scoring_service=mock_scoring_service,
        qa_repository=mock_qa_repository,
    )
    
    # 답변 생성
    result = await qa_service.answer_question(qa_id=1)
    
    # 검증
    assert result["qa_id"] == 1
    assert result["predicted_answer"] == "2"
    assert result["is_correct"] is True
    assert result["score"] == 1.0
    assert "meta" in result
    
    # 모의 객체 호출 확인
    mock_qa_repository.get_qa_by_id.assert_called_once_with(1)
    mock_llm_service.generate_completion.assert_called_once()
    mock_qa_repository.create_attempt_log.assert_called_once()


@pytest.mark.asyncio
async def test_answer_question_with_text(
    settings,
    mock_llm_service,
    mock_scoring_service,
    mock_qa_repository,
):
    """
    직접 입력한 문제로 답변 생성 테스트
    """
    qa_service = QAService(
        settings=settings,
        llm_service=mock_llm_service,
        scoring_service=mock_scoring_service,
        qa_repository=mock_qa_repository,
    )
    
    # 답변 생성
    result = await qa_service.answer_question(
        question="당뇨병의 3대 증상은?"
    )
    
    # 검증
    assert result["qa_id"] is None
    assert result["question"] == "당뇨병의 3대 증상은?"
    assert result["predicted_answer"] == "2"
    assert "meta" in result


@pytest.mark.asyncio
async def test_answer_question_no_input():
    """
    qa_id와 question이 모두 없을 때 에러 테스트
    """
    settings = get_settings()
    qa_service = QAService(
        settings=settings,
        llm_service=Mock(),
        scoring_service=Mock(),
        qa_repository=Mock(spec=QARepository),
    )
    
    # 예외 발생 확인
    with pytest.raises(ValueError):
        await qa_service.answer_question()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
