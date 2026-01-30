"""
QA Routes
기능1: 문제 답변 생성 및 채점 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import QARequest, QAResponse, ErrorResponse, ErrorDetail
from app.services import QAService, LLMService, ScoringService
from app.api.dependencies import (
    get_db_session,
    get_llm_service,
    get_scoring_service,
    get_qa_service,
)
from app.utils import generate_trace_id, RequestLogger

router = APIRouter(prefix="/qa", tags=["QA"])


@router.post(
    "/answer",
    response_model=QAResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    }
)
async def answer_question(
    request: QARequest,
    session: AsyncSession = Depends(get_db_session),
    llm_service: LLMService = Depends(get_llm_service),
    scoring_service: ScoringService = Depends(get_scoring_service),
):
    """
    문제에 대한 답변 생성 및 채점
    
    **처리 흐름:**
    1. 문제 조회 (qa_id) 또는 직접 입력 (question)
    2. LLM으로 답변 생성
    3. 정답과 비교하여 채점 (정답이 있는 경우)
    4. 결과 및 로그 저장
    
    **입력:**
    - `qa_id` (선택): 데이터베이스에 저장된 문제 ID
    - `question` (선택): 직접 입력한 문제 (qa_id가 없는 경우 필수)
    
    **출력:**
    - 예측 답변
    - 정답 여부 (정답이 있는 경우)
    - 점수 (0.0 ~ 1.0)
    - 채점 설명
    - 메타데이터 (모델, 응답시간 등)
    
    **예시:**
    ```json
    {
      "qa_id": 1
    }
    ```
    
    또는
    
    ```json
    {
      "question": "급성 심근경색의 주요 증상 3가지는?"
    }
    ```
    """
    trace_id = generate_trace_id()
    req_logger = RequestLogger(trace_id)
    
    req_logger.log_request(
        method="POST",
        path="/qa/answer",
        qa_id=request.qa_id,
        has_question=bool(request.question),
    )
    
    try:
        # QA 서비스 생성
        qa_service = get_qa_service(session, llm_service, scoring_service)
        
        # 답변 생성 및 채점
        result = await qa_service.answer_question(
            qa_id=request.qa_id,
            question=request.question,
            trace_id=trace_id,
        )
        
        req_logger.log_response(status_code=200)
        
        return QAResponse(**result)
    
    except ValueError as e:
        req_logger.log_error(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    except Exception as e:
        req_logger.log_error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="답변 생성 중 오류가 발생했습니다",
        )
