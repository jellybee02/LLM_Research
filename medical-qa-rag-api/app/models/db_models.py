"""
SQLAlchemy Database Models
PostgreSQL 데이터베이스 모델
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class QAMaster(Base):
    """
    문제/정답 마스터 테이블
    기능1: QA Answering용 문제 저장
    """
    __tablename__ = "qa_master"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(100), nullable=True, index=True, comment="도메인/카테고리")
    q_type = Column(String(50), nullable=False, comment="문제 유형 (multiple_choice, short_answer, essay)")
    question = Column(Text, nullable=False, comment="문제 본문")
    answer = Column(Text, nullable=False, comment="정답")
    choices = Column(JSON, nullable=True, comment="선택지 (객관식용)")
    explanation = Column(Text, nullable=True, comment="해설")
    metadata = Column(JSON, nullable=True, comment="추가 메타데이터")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index("ix_qa_master_domain_qtype", "domain", "q_type"),
    )
    
    def __repr__(self):
        return f"<QAMaster(id={self.id}, domain={self.domain}, q_type={self.q_type})>"


class QAAttemptLog(Base):
    """
    QA 시도 로그 테이블
    사용자의 문제 풀이 시도 및 채점 결과 저장
    """
    __tablename__ = "qa_attempt_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    qa_id = Column(Integer, nullable=True, index=True, comment="문제 ID (qa_master 참조)")
    question = Column(Text, nullable=False, comment="문제 텍스트")
    predicted_answer = Column(Text, nullable=False, comment="모델 예측 답변")
    correct_answer = Column(Text, nullable=True, comment="정답")
    is_correct = Column(Boolean, nullable=True, comment="정답 여부")
    score = Column(Float, nullable=True, comment="점수 (0.0 ~ 1.0)")
    
    # 모델 및 설정
    model = Column(String(100), nullable=False, comment="사용된 모델")
    prompt_version = Column(String(50), nullable=False, comment="프롬프트 버전")
    
    # 성능 메트릭
    latency_ms = Column(Integer, nullable=False, comment="응답 시간 (밀리초)")
    tokens_used = Column(Integer, nullable=True, comment="사용된 토큰 수")
    
    # 추적 및 감사
    trace_id = Column(String(100), nullable=False, index=True, comment="요청 추적 ID")
    user_id = Column(String(100), nullable=True, index=True, comment="사용자 ID (익명화)")
    session_id = Column(String(100), nullable=True, index=True, comment="세션 ID")
    
    metadata = Column(JSON, nullable=True, comment="추가 메타데이터")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index("ix_qa_attempt_created", "created_at"),
        Index("ix_qa_attempt_trace", "trace_id"),
    )
    
    def __repr__(self):
        return f"<QAAttemptLog(id={self.id}, qa_id={self.qa_id}, is_correct={self.is_correct})>"


class RAGAttemptLog(Base):
    """
    RAG 시도 로그 테이블
    RAG 기반 답변 생성 기록 저장
    """
    __tablename__ = "rag_attempt_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False, comment="사용자 질문")
    department = Column(String(20), nullable=False, index=True, comment="분류된 진료과")
    answer = Column(Text, nullable=False, comment="생성된 답변")
    
    # 참조 문서
    references = Column(JSON, nullable=False, comment="참조 문서 목록")
    confidence = Column(Float, nullable=True, comment="답변 신뢰도")
    
    # 모델 및 설정
    model = Column(String(100), nullable=False, comment="사용된 모델")
    prompt_version = Column(String(50), nullable=False, comment="프롬프트 버전")
    
    # 성능 메트릭
    latency_ms = Column(Integer, nullable=False, comment="응답 시간 (밀리초)")
    tokens_used = Column(Integer, nullable=True, comment="사용된 토큰 수")
    
    # 검색 메트릭
    search_results_count = Column(Integer, nullable=True, comment="검색된 문서 수")
    avg_search_score = Column(Float, nullable=True, comment="평균 검색 점수")
    
    # 추적 및 감사
    trace_id = Column(String(100), nullable=False, index=True, comment="요청 추적 ID")
    user_id = Column(String(100), nullable=True, index=True, comment="사용자 ID (익명화)")
    session_id = Column(String(100), nullable=True, index=True, comment="세션 ID")
    
    metadata = Column(JSON, nullable=True, comment="추가 메타데이터")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index("ix_rag_attempt_created", "created_at"),
        Index("ix_rag_attempt_department", "department"),
        Index("ix_rag_attempt_trace", "trace_id"),
    )
    
    def __repr__(self):
        return f"<RAGAttemptLog(id={self.id}, department={self.department})>"


class AuditLog(Base):
    """
    통합 감사 로그 테이블
    모든 중요 작업에 대한 감사 추적
    """
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True, comment="이벤트 타입 (qa_request, rag_request, etc)")
    action = Column(String(100), nullable=False, comment="수행된 작업")
    
    # 요청 정보
    trace_id = Column(String(100), nullable=False, index=True, comment="요청 추적 ID")
    user_id = Column(String(100), nullable=True, index=True, comment="사용자 ID (익명화)")
    ip_address = Column(String(45), nullable=True, comment="IP 주소 (IPv6 지원)")
    user_agent = Column(Text, nullable=True, comment="User Agent")
    
    # 요청/응답 데이터 (PII 마스킹 후 저장)
    request_data = Column(JSON, nullable=True, comment="요청 데이터 (마스킹)")
    response_data = Column(JSON, nullable=True, comment="응답 데이터 (마스킹)")
    
    # 결과
    status = Column(String(20), nullable=False, comment="성공/실패 상태")
    error_message = Column(Text, nullable=True, comment="에러 메시지")
    
    metadata = Column(JSON, nullable=True, comment="추가 메타데이터")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index("ix_audit_log_created", "created_at"),
        Index("ix_audit_log_event", "event_type", "created_at"),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, status={self.status})>"
