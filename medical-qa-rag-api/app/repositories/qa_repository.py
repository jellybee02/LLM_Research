"""
QA Repository
QA 관련 데이터베이스 접근
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import QAMaster, QAAttemptLog
from app.utils import get_logger

logger = get_logger(__name__)


class QARepository:
    """
    QA 데이터베이스 레포지토리
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_qa_by_id(self, qa_id: int) -> Optional[QAMaster]:
        """
        ID로 문제 조회
        
        Args:
            qa_id: 문제 ID
            
        Returns:
            QAMaster 또는 None
        """
        try:
            stmt = select(QAMaster).where(QAMaster.id == qa_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("get_qa_by_id_error", qa_id=qa_id, error=str(e))
            return None
    
    async def get_qa_by_domain(
        self,
        domain: str,
        limit: int = 10
    ) -> List[QAMaster]:
        """
        도메인별 문제 조회
        
        Args:
            domain: 도메인명
            limit: 결과 제한
            
        Returns:
            문제 리스트
        """
        try:
            stmt = select(QAMaster).where(
                QAMaster.domain == domain
            ).limit(limit)
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("get_qa_by_domain_error", domain=domain, error=str(e))
            return []
    
    async def create_qa(
        self,
        domain: Optional[str],
        q_type: str,
        question: str,
        answer: str,
        choices: Optional[List[str]] = None,
        explanation: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[QAMaster]:
        """
        새 문제 생성
        
        Args:
            domain: 도메인
            q_type: 문제 유형
            question: 문제
            answer: 정답
            choices: 선택지
            explanation: 해설
            metadata: 메타데이터
            
        Returns:
            생성된 QAMaster 또는 None
        """
        try:
            qa = QAMaster(
                domain=domain,
                q_type=q_type,
                question=question,
                answer=answer,
                choices=choices,
                explanation=explanation,
                metadata=metadata,
            )
            self.session.add(qa)
            await self.session.commit()
            await self.session.refresh(qa)
            
            logger.info("qa_created", qa_id=qa.id)
            return qa
        except Exception as e:
            await self.session.rollback()
            logger.error("create_qa_error", error=str(e))
            return None
    
    async def create_attempt_log(
        self,
        qa_id: Optional[int],
        question: str,
        predicted_answer: str,
        correct_answer: Optional[str],
        is_correct: Optional[bool],
        score: Optional[float],
        model: str,
        prompt_version: str,
        latency_ms: int,
        trace_id: str,
        tokens_used: Optional[int] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[QAAttemptLog]:
        """
        QA 시도 로그 생성
        
        Args:
            qa_id: 문제 ID
            question: 문제
            predicted_answer: 예측 답변
            correct_answer: 정답
            is_correct: 정답 여부
            score: 점수
            model: 모델명
            prompt_version: 프롬프트 버전
            latency_ms: 응답 시간
            trace_id: 추적 ID
            tokens_used: 사용 토큰 수
            user_id: 사용자 ID
            session_id: 세션 ID
            metadata: 메타데이터
            
        Returns:
            생성된 QAAttemptLog 또는 None
        """
        try:
            log = QAAttemptLog(
                qa_id=qa_id,
                question=question,
                predicted_answer=predicted_answer,
                correct_answer=correct_answer,
                is_correct=is_correct,
                score=score,
                model=model,
                prompt_version=prompt_version,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                trace_id=trace_id,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata,
            )
            self.session.add(log)
            await self.session.commit()
            await self.session.refresh(log)
            
            logger.info("qa_attempt_log_created", log_id=log.id, trace_id=trace_id)
            return log
        except Exception as e:
            await self.session.rollback()
            logger.error("create_attempt_log_error", trace_id=trace_id, error=str(e))
            return None
    
    async def get_attempt_logs_by_trace(
        self,
        trace_id: str
    ) -> List[QAAttemptLog]:
        """
        추적 ID로 로그 조회
        
        Args:
            trace_id: 추적 ID
            
        Returns:
            로그 리스트
        """
        try:
            stmt = select(QAAttemptLog).where(
                QAAttemptLog.trace_id == trace_id
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("get_attempt_logs_error", trace_id=trace_id, error=str(e))
            return []
