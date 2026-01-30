"""
Pydantic Schemas for API Request/Response
API 요청/응답 데이터 모델
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


# 진료과 코드
class DepartmentCode(str, Enum):
    EM = "EM"  # Emergency Medicine
    IM = "IM"  # Internal Medicine
    PED = "PED"  # Pediatrics
    OBGYN = "OBGYN"  # Obstetrics & Gynecology
    COMMON = "COMMON"  # General


# 문제 유형
class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"


# ========== 기능1: QA Answering ==========

class QARequest(BaseModel):
    """QA 요청"""
    qa_id: Optional[int] = Field(None, description="문제 ID (qa_id 또는 question 중 하나 필수)")
    question: Optional[str] = Field(None, description="문제 텍스트 (qa_id가 없을 경우)")
    
    @validator('question')
    def validate_question(cls, v, values):
        if 'qa_id' not in values or values['qa_id'] is None:
            if not v:
                raise ValueError("qa_id 또는 question 중 하나는 필수입니다")
        return v


class QAResponse(BaseModel):
    """QA 응답"""
    trace_id: str = Field(..., description="요청 추적 ID")
    qa_id: Optional[int] = Field(None, description="문제 ID")
    question: str = Field(..., description="문제 텍스트")
    predicted_answer: str = Field(..., description="모델이 예측한 답변")
    correct_answer: Optional[str] = Field(None, description="정답")
    is_correct: Optional[bool] = Field(None, description="정답 여부")
    score: Optional[float] = Field(None, description="점수 (0.0 ~ 1.0)")
    explanation: Optional[str] = Field(None, description="채점 설명")
    meta: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trace_id": "req_123456",
                "qa_id": 1,
                "question": "급성 심근경색의 주요 증상은?",
                "predicted_answer": "흉통, 호흡곤란",
                "correct_answer": "흉통, 호흡곤란, 발한",
                "is_correct": False,
                "score": 0.67,
                "explanation": "주요 증상은 맞췄으나 발한을 누락",
                "meta": {
                    "model": "gpt-4-turbo-preview",
                    "latency_ms": 1234,
                    "tokens_used": 150
                }
            }
        }


# ========== 기능2: RAG ==========

class RAGRequest(BaseModel):
    """RAG 요청"""
    question: str = Field(..., description="의료 관련 질문", min_length=1, max_length=2000)
    department: Optional[DepartmentCode] = Field(None, description="진료과 (자동 분류 또는 수동 지정)")
    patient_info: Optional[Dict[str, Any]] = Field(None, description="환자 정보 (나이, 성별 등)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "급성 흉통이 있을 때 어떻게 해야 하나요?",
                "patient_info": {
                    "age": 45,
                    "gender": "male"
                }
            }
        }


class DocumentReference(BaseModel):
    """참조 문서 정보"""
    doc_id: str = Field(..., description="문서 ID")
    title: Optional[str] = Field(None, description="문서 제목")
    content: str = Field(..., description="관련 내용")
    score: float = Field(..., description="유사도 점수")
    source: Optional[str] = Field(None, description="출처")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")


class RAGResponse(BaseModel):
    """RAG 응답"""
    trace_id: str = Field(..., description="요청 추적 ID")
    question: str = Field(..., description="질문")
    department: DepartmentCode = Field(..., description="분류된 진료과")
    answer: str = Field(..., description="생성된 답변")
    references: List[DocumentReference] = Field(default_factory=list, description="참조 문서 목록")
    confidence: Optional[float] = Field(None, description="답변 신뢰도 (0.0 ~ 1.0)")
    warnings: List[str] = Field(default_factory=list, description="경고 메시지")
    meta: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trace_id": "req_789012",
                "question": "급성 흉통이 있을 때 어떻게 해야 하나요?",
                "department": "EM",
                "answer": "급성 흉통은 심근경색의 주요 증상일 수 있어 즉시 응급실 방문이 필요합니다...",
                "references": [
                    {
                        "doc_id": "doc_001",
                        "title": "급성 관상동맥 증후군 가이드라인",
                        "content": "...",
                        "score": 0.92,
                        "source": "대한심장학회"
                    }
                ],
                "confidence": 0.89,
                "warnings": ["즉시 119에 연락하거나 응급실을 방문하세요"],
                "meta": {
                    "model": "gpt-4-turbo-preview",
                    "latency_ms": 2345,
                    "prompt_version": "1.0.0"
                }
            }
        }


# ========== 공통 응답 ==========

class ErrorDetail(BaseModel):
    """에러 상세 정보"""
    code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 설명")


class ErrorResponse(BaseModel):
    """에러 응답"""
    trace_id: str = Field(..., description="요청 추적 ID")
    error: ErrorDetail = Field(..., description="에러 정보")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="발생 시각")


class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str = Field(..., description="서비스 상태")
    version: str = Field(..., description="API 버전")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="응답 시각")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="의존성 서비스 상태")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-01-15T10:30:00Z",
                "dependencies": {
                    "database": "healthy",
                    "qdrant": "healthy",
                    "openai": "healthy"
                }
            }
        }


# ========== DB 모델용 스키마 ==========

class QAMasterCreate(BaseModel):
    """QA 문제 생성"""
    domain: Optional[str] = None
    q_type: QuestionType
    question: str
    answer: str
    choices: Optional[List[str]] = None
    explanation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class QAAttemptLog(BaseModel):
    """QA 시도 로그"""
    qa_id: Optional[int]
    question: str
    predicted_answer: str
    correct_answer: Optional[str]
    is_correct: Optional[bool]
    score: Optional[float]
    model: str
    prompt_version: str
    latency_ms: int
    trace_id: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RAGAttemptLog(BaseModel):
    """RAG 시도 로그"""
    question: str
    department: DepartmentCode
    answer: str
    references: List[Dict[str, Any]]
    model: str
    prompt_version: str
    latency_ms: int
    trace_id: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
