"""
Logging Utilities
구조화된 로깅 및 감사 로그 유틸리티
"""

import logging
import json
import uuid
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path
import structlog


def setup_logging(config):
    """
    로깅 설정 초기화
    """
    log_level = getattr(logging, config.logging.level.upper())
    
    # 로그 디렉토리 생성
    if config.logging.file.enabled:
        log_path = Path(config.logging.file.path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 기본 로깅 설정
    logging.basicConfig(
        level=log_level,
        format="%(message)s"
    )
    
    # structlog 설정
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if config.logging.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """
    구조화된 로거 반환
    """
    return structlog.get_logger(name)


def generate_trace_id() -> str:
    """
    요청 추적 ID 생성
    """
    return f"req_{uuid.uuid4().hex[:12]}"


class RequestLogger:
    """
    요청 로깅 헬퍼
    """
    
    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.logger = get_logger("api.request")
        self.start_time = datetime.utcnow()
    
    def log_request(self, method: str, path: str, **kwargs):
        """요청 로깅"""
        self.logger.info(
            "request_received",
            trace_id=self.trace_id,
            method=method,
            path=path,
            **kwargs
        )
    
    def log_response(self, status_code: int, **kwargs):
        """응답 로깅"""
        end_time = datetime.utcnow()
        latency_ms = int((end_time - self.start_time).total_seconds() * 1000)
        
        self.logger.info(
            "request_completed",
            trace_id=self.trace_id,
            status_code=status_code,
            latency_ms=latency_ms,
            **kwargs
        )
    
    def log_error(self, error: Exception, **kwargs):
        """에러 로깅"""
        self.logger.error(
            "request_error",
            trace_id=self.trace_id,
            error=str(error),
            error_type=type(error).__name__,
            **kwargs
        )


class AuditLogger:
    """
    감사 로그 헬퍼
    의료 데이터 접근/수정에 대한 감사 추적
    """
    
    def __init__(self):
        self.logger = get_logger("audit")
    
    def log_qa_attempt(
        self,
        trace_id: str,
        qa_id: Optional[int],
        question: str,
        predicted_answer: str,
        is_correct: Optional[bool],
        user_id: Optional[str] = None,
        **kwargs
    ):
        """QA 시도 감사 로그"""
        self.logger.info(
            "qa_attempt",
            event_type="qa_request",
            trace_id=trace_id,
            qa_id=qa_id,
            question_length=len(question),
            answer_length=len(predicted_answer),
            is_correct=is_correct,
            user_id=user_id,
            **kwargs
        )
    
    def log_rag_attempt(
        self,
        trace_id: str,
        question: str,
        department: str,
        answer: str,
        references_count: int,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """RAG 시도 감사 로그"""
        self.logger.info(
            "rag_attempt",
            event_type="rag_request",
            trace_id=trace_id,
            question_length=len(question),
            department=department,
            answer_length=len(answer),
            references_count=references_count,
            user_id=user_id,
            **kwargs
        )
    
    def log_data_access(
        self,
        trace_id: str,
        resource: str,
        action: str,
        user_id: Optional[str] = None,
        **kwargs
    ):
        """데이터 접근 감사 로그"""
        self.logger.info(
            "data_access",
            event_type="data_access",
            trace_id=trace_id,
            resource=resource,
            action=action,
            user_id=user_id,
            **kwargs
        )
    
    def log_security_event(
        self,
        trace_id: str,
        event: str,
        severity: str = "info",
        **kwargs
    ):
        """보안 이벤트 로그"""
        log_func = getattr(self.logger, severity.lower(), self.logger.info)
        log_func(
            "security_event",
            event_type="security",
            trace_id=trace_id,
            event=event,
            **kwargs
        )


# 전역 감사 로거
audit_logger = AuditLogger()
