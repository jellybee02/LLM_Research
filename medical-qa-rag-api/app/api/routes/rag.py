"""
RAG Routes
기능2: 진료과 분류 + RAG 기반 전문 답변 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RAGRequest, RAGResponse, ErrorResponse, DepartmentCode
from app.services import RAGService, LLMService, QdrantService, RouterService
from app.api.dependencies import (
    get_db_session,
    get_llm_service,
    get_qdrant_service,
    get_router_service,
    get_rag_service,
)
from app.utils import generate_trace_id, RequestLogger, sanitize_user_input

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post(
    "/answer",
    response_model=RAGResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    }
)
async def answer_with_rag(
    request: RAGRequest,
    session: AsyncSession = Depends(get_db_session),
    llm_service: LLMService = Depends(get_llm_service),
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    router_service: RouterService = Depends(get_router_service),
):
    """
    RAG 기반 의료 질의응답
    
    **처리 흐름:**
    1. 질문을 적절한 진료과로 자동 분류 (또는 수동 지정)
       - 응급의학과 (EM)
       - 내과 (IM)
       - 소아청소년과 (PED)
       - 산부인과 (OBGYN)
       - 공용 (COMMON)
    2. 해당 진료과의 전문 문서에서 관련 내용 검색
    3. 검색된 문서를 근거로 전문 답변 생성
    4. 안전성 체크 및 경고 메시지 추가
    5. 결과 및 로그 저장
    
    **입력:**
    - `question` (필수): 의료 관련 질문
    - `department` (선택): 수동으로 진료과 지정 (자동 분류 생략)
    - `patient_info` (선택): 환자 정보 (나이, 성별, 기저질환 등)
    
    **출력:**
    - 생성된 답변
    - 분류된 진료과
    - 참조 문서 목록 (출처, 내용, 유사도 점수)
    - 신뢰도 점수
    - 경고 메시지 (필요시)
    - 메타데이터
    
    **예시:**
    ```json
    {
      "question": "급성 흉통이 있을 때 어떻게 해야 하나요?",
      "patient_info": {
        "age": 45,
        "gender": "male"
      }
    }
    ```
    
    **주의사항:**
    - 본 서비스는 참고용이며, 정확한 진단과 처방은 의료기관을 방문하여 받으시기 바랍니다.
    - 응급 상황 시 즉시 119에 연락하거나 응급실을 방문하세요.
    """
    trace_id = generate_trace_id()
    req_logger = RequestLogger(trace_id)
    
    # 입력 정제
    question = sanitize_user_input(request.question, max_length=2000)
    
    req_logger.log_request(
        method="POST",
        path="/rag/answer",
        question_length=len(question),
        department=request.department.value if request.department else None,
    )
    
    try:
        # RAG 서비스 생성
        rag_service = get_rag_service(
            session,
            llm_service,
            qdrant_service,
            router_service,
        )
        
        # 답변 생성
        result = await rag_service.answer_with_rag(
            question=question,
            department=request.department,
            patient_info=request.patient_info,
            trace_id=trace_id,
        )
        
        req_logger.log_response(
            status_code=200,
            department=result["department"],
            references_count=len(result["references"]),
        )
        
        return RAGResponse(**result)
    
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


@router.post(
    "/classify",
    status_code=status.HTTP_200_OK,
)
async def classify_department(
    question: str,
    router_service: RouterService = Depends(get_router_service),
):
    """
    질문을 진료과로 분류 (테스트용 엔드포인트)
    
    **입력:**
    - `question`: 분류할 질문
    
    **출력:**
    - 분류된 진료과 코드
    
    **예시:**
    ```
    POST /rag/classify
    {
      "question": "임신 중 복용 가능한 감기약은?"
    }
    
    Response:
    {
      "question": "임신 중 복용 가능한 감기약은?",
      "department": "OBGYN"
    }
    ```
    """
    trace_id = generate_trace_id()
    req_logger = RequestLogger(trace_id)
    
    question = sanitize_user_input(question, max_length=2000)
    
    req_logger.log_request(
        method="POST",
        path="/rag/classify",
        question_length=len(question),
    )
    
    try:
        department = await router_service.route_question(question)
        
        req_logger.log_response(
            status_code=200,
            department=department.value,
        )
        
        return {
            "question": question,
            "department": department.value,
        }
    
    except Exception as e:
        req_logger.log_error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="진료과 분류 중 오류가 발생했습니다",
        )
