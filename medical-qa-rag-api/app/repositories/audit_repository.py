"""
Audit Repository
감사 로그 및 RAG 로그 데이터베이스 접근
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import RAGAttemptLog, AuditLog
from app.utils import get_logger

logger = get_logger(__name__)


class AuditRepository:
    """
    감사 로그 데이터베이스 레포지토리
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_rag_log(
        self,
        question: str,
        department: str,
        answer: str,
        references: List[Dict[str, Any]],
        model: str,
        prompt_version: str,
        latency_ms: int,
        trace_id: str,
        tokens_used: Optional[int] = None,
        confidence: Optional[float] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[RAGAttemptLog]:
        """
        RAG 시도 로그 생성
        
        Args:
            question: 질문
            department: 진료과
            answer: 답변
            references: 참조 문서
            model: 모델명
            prompt_version: 프롬프트 버전
            latency_ms: 응답 시간
            trace_id: 추적 ID
            tokens_used: 사용 토큰 수
            confidence: 신뢰도
            user_id: 사용자 ID
            session_id: 세션 ID
            metadata: 메타데이터
            
        Returns:
            생성된 RAGAttemptLog 또는 None
        """
        try:
            # 검색 메트릭 계산
            search_results_count = len(references)
            avg_search_score = (
                sum(ref.get("score", 0) for ref in references) / search_results_count
                if search_results_count > 0
                else None
            )
            
            log = RAGAttemptLog(
                question=question,
                department=department,
                answer=answer,
                references=references,
                confidence=confidence,
                model=model,
                prompt_version=prompt_version,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                search_results_count=search_results_count,
                avg_search_score=avg_search_score,
                trace_id=trace_id,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata,
            )
            self.session.add(log)
            await self.session.commit()
            await self.session.refresh(log)
            
            logger.info("rag_log_created", log_id=log.id, trace_id=trace_id)
            return log
        except Exception as e:
            await self.session.rollback()
            logger.error("create_rag_log_error", trace_id=trace_id, error=str(e))
            return None
    
    async def create_audit_log(
        self,
        event_type: str,
        action: str,
        trace_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_data: Optional[dict] = None,
        response_data: Optional[dict] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[AuditLog]:
        """
        감사 로그 생성
        
        Args:
            event_type: 이벤트 타입
            action: 수행 작업
            trace_id: 추적 ID
            user_id: 사용자 ID
            ip_address: IP 주소
            user_agent: User Agent
            request_data: 요청 데이터
            response_data: 응답 데이터
            status: 상태
            error_message: 에러 메시지
            metadata: 메타데이터
            
        Returns:
            생성된 AuditLog 또는 None
        """
        try:
            log = AuditLog(
                event_type=event_type,
                action=action,
                trace_id=trace_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_data=request_data,
                response_data=response_data,
                status=status,
                error_message=error_message,
                metadata=metadata,
            )
            self.session.add(log)
            await self.session.commit()
            await self.session.refresh(log)
            
            logger.info("audit_log_created", log_id=log.id, event_type=event_type)
            return log
        except Exception as e:
            await self.session.rollback()
            logger.error("create_audit_log_error", event_type=event_type, error=str(e))
            return None
    
    async def get_rag_logs_by_trace(
        self,
        trace_id: str
    ) -> List[RAGAttemptLog]:
        """
        추적 ID로 RAG 로그 조회
        
        Args:
            trace_id: 추적 ID
            
        Returns:
            로그 리스트
        """
        try:
            stmt = select(RAGAttemptLog).where(
                RAGAttemptLog.trace_id == trace_id
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("get_rag_logs_error", trace_id=trace_id, error=str(e))
            return []
    
    async def get_rag_logs_by_department(
        self,
        department: str,
        limit: int = 100
    ) -> List[RAGAttemptLog]:
        """
        진료과별 RAG 로그 조회
        
        Args:
            department: 진료과
            limit: 결과 제한
            
        Returns:
            로그 리스트
        """
        try:
            stmt = select(RAGAttemptLog).where(
                RAGAttemptLog.department == department
            ).order_by(
                RAGAttemptLog.created_at.desc()
            ).limit(limit)
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("get_rag_logs_by_department_error", department=department, error=str(e))
            return []
    
    async def get_audit_logs_by_user(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        사용자별 감사 로그 조회
        
        Args:
            user_id: 사용자 ID
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 결과 제한
            
        Returns:
            로그 리스트
        """
        try:
            stmt = select(AuditLog).where(AuditLog.user_id == user_id)
            
            if start_date:
                stmt = stmt.where(AuditLog.created_at >= start_date)
            if end_date:
                stmt = stmt.where(AuditLog.created_at <= end_date)
            
            stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("get_audit_logs_by_user_error", user_id=user_id, error=str(e))
            return []
