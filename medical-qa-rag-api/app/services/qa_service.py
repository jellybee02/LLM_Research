"""
QA Service
기능1: 문제 답변 생성 및 채점
"""

import time
from typing import Dict, Any, Optional

from app.config import Settings
from app.models import DepartmentCode
from app.services.llm_service import LLMService
from app.services.scoring_service import ScoringService
from app.repositories.qa_repository import QARepository
from app.utils import get_logger, PromptBuilder, generate_trace_id

logger = get_logger(__name__)


class QAService:
    """
    QA 답변 생성 및 채점 서비스
    """
    
    def __init__(
        self,
        settings: Settings,
        llm_service: LLMService,
        scoring_service: ScoringService,
        qa_repository: QARepository,
    ):
        self.settings = settings
        self.llm_service = llm_service
        self.scoring_service = scoring_service
        self.qa_repository = qa_repository
        self.prompt_builder = PromptBuilder(settings)
    
    async def answer_question(
        self,
        qa_id: Optional[int] = None,
        question: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        문제에 대한 답변 생성 및 채점
        
        Args:
            qa_id: 문제 ID (DB 조회용)
            question: 문제 텍스트 (직접 입력)
            trace_id: 요청 추적 ID
            
        Returns:
            {
                "trace_id": str,
                "qa_id": int | None,
                "question": str,
                "predicted_answer": str,
                "correct_answer": str | None,
                "is_correct": bool | None,
                "score": float | None,
                "explanation": str | None,
                "meta": dict
            }
        """
        start_time = time.time()
        trace_id = trace_id or generate_trace_id()
        
        # 문제 조회
        qa_data = await self._get_qa_data(qa_id, question)
        
        if not qa_data:
            raise ValueError("문제를 찾을 수 없습니다")
        
        # 답변 생성
        try:
            predicted_answer = await self._generate_answer(qa_data["question"])
        except Exception as e:
            logger.error(
                "answer_generation_error",
                trace_id=trace_id,
                error=str(e),
            )
            raise
        
        # 채점 (정답이 있는 경우)
        scoring_result = None
        if qa_data.get("answer"):
            scoring_result = self.scoring_service.score_answer(
                predicted=predicted_answer,
                correct=qa_data["answer"],
                q_type=qa_data.get("q_type", "short_answer"),
            )
        
        # 응답 시간 계산
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 로그 저장
        await self._save_attempt_log(
            trace_id=trace_id,
            qa_id=qa_data.get("id"),
            question=qa_data["question"],
            predicted_answer=predicted_answer,
            correct_answer=qa_data.get("answer"),
            scoring_result=scoring_result,
            latency_ms=latency_ms,
        )
        
        # 결과 반환
        result = {
            "trace_id": trace_id,
            "qa_id": qa_data.get("id"),
            "question": qa_data["question"],
            "predicted_answer": predicted_answer,
            "correct_answer": qa_data.get("answer"),
            "is_correct": scoring_result["is_correct"] if scoring_result else None,
            "score": scoring_result["score"] if scoring_result else None,
            "explanation": scoring_result.get("explanation") if scoring_result else None,
            "meta": {
                "model": self.settings.openai.model,
                "prompt_version": self.prompt_builder.get_prompt_version(),
                "latency_ms": latency_ms,
                "q_type": qa_data.get("q_type"),
            }
        }
        
        logger.info(
            "qa_completed",
            trace_id=trace_id,
            qa_id=qa_data.get("id"),
            is_correct=result["is_correct"],
            latency_ms=latency_ms,
        )
        
        return result
    
    async def _get_qa_data(
        self,
        qa_id: Optional[int],
        question: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        문제 데이터 조회
        
        Args:
            qa_id: 문제 ID
            question: 문제 텍스트
            
        Returns:
            문제 데이터 또는 None
        """
        # qa_id가 있으면 DB에서 조회
        if qa_id:
            qa_master = await self.qa_repository.get_qa_by_id(qa_id)
            if qa_master:
                return {
                    "id": qa_master.id,
                    "question": qa_master.question,
                    "answer": qa_master.answer,
                    "q_type": qa_master.q_type,
                    "domain": qa_master.domain,
                    "choices": qa_master.choices,
                }
        
        # question만 있으면 그대로 사용
        if question:
            return {
                "id": None,
                "question": question,
                "answer": None,
                "q_type": "short_answer",
            }
        
        return None
    
    async def _generate_answer(self, question: str) -> str:
        """
        LLM을 사용한 답변 생성
        
        Args:
            question: 문제 텍스트
            
        Returns:
            생성된 답변
        """
        messages = self.prompt_builder.build_qa_prompt(question)
        
        result = await self.llm_service.generate_completion(messages)
        
        return result["content"].strip()
    
    async def _save_attempt_log(
        self,
        trace_id: str,
        qa_id: Optional[int],
        question: str,
        predicted_answer: str,
        correct_answer: Optional[str],
        scoring_result: Optional[Dict[str, Any]],
        latency_ms: int,
    ):
        """
        QA 시도 로그 저장
        
        Args:
            trace_id: 추적 ID
            qa_id: 문제 ID
            question: 문제
            predicted_answer: 예측 답변
            correct_answer: 정답
            scoring_result: 채점 결과
            latency_ms: 응답 시간
        """
        try:
            await self.qa_repository.create_attempt_log(
                qa_id=qa_id,
                question=question,
                predicted_answer=predicted_answer,
                correct_answer=correct_answer,
                is_correct=scoring_result["is_correct"] if scoring_result else None,
                score=scoring_result["score"] if scoring_result else None,
                model=self.settings.openai.model,
                prompt_version=self.prompt_builder.get_prompt_version(),
                latency_ms=latency_ms,
                trace_id=trace_id,
            )
        except Exception as e:
            logger.error(
                "save_attempt_log_error",
                trace_id=trace_id,
                error=str(e),
            )
