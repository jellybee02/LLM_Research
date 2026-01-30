"""
RAG Service
기능2: 진료과 분류 + RAG 기반 전문 답변 생성
"""

import time
from typing import Dict, Any, List, Optional

from app.config import Settings
from app.models import DepartmentCode, DocumentReference
from app.services.llm_service import LLMService
from app.services.qdrant_service import QdrantService
from app.services.router_service import RouterService
from app.repositories.audit_repository import AuditRepository
from app.utils import get_logger, PromptBuilder, generate_trace_id

logger = get_logger(__name__)


class RAGService:
    """
    RAG 기반 의료 질의응답 서비스
    """
    
    def __init__(
        self,
        settings: Settings,
        llm_service: LLMService,
        qdrant_service: QdrantService,
        router_service: RouterService,
        audit_repository: AuditRepository,
    ):
        self.settings = settings
        self.llm_service = llm_service
        self.qdrant_service = qdrant_service
        self.router_service = router_service
        self.audit_repository = audit_repository
        self.prompt_builder = PromptBuilder(settings)
    
    async def answer_with_rag(
        self,
        question: str,
        department: Optional[DepartmentCode] = None,
        patient_info: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        RAG 기반 답변 생성
        
        처리 흐름:
        1. 진료과 분류 (지정되지 않은 경우)
        2. 질문 임베딩
        3. 관련 문서 검색
        4. 답변 생성
        5. 로그 저장
        
        Args:
            question: 사용자 질문
            department: 진료과 (None이면 자동 분류)
            patient_info: 환자 정보 (선택)
            trace_id: 요청 추적 ID
            
        Returns:
            {
                "trace_id": str,
                "question": str,
                "department": str,
                "answer": str,
                "references": List[DocumentReference],
                "confidence": float | None,
                "warnings": List[str],
                "meta": dict
            }
        """
        start_time = time.time()
        trace_id = trace_id or generate_trace_id()
        
        warnings = []
        
        # 1. 진료과 분류
        if not department:
            department = await self.router_service.route_question(question)
            logger.info(
                "department_classified",
                trace_id=trace_id,
                department=department.value,
            )
        
        # 2. 질문 임베딩
        try:
            query_embedding = await self.llm_service.generate_embedding(question)
        except Exception as e:
            logger.error(
                "embedding_error",
                trace_id=trace_id,
                error=str(e),
            )
            raise
        
        # 3. 관련 문서 검색
        retrieved_docs = await self.qdrant_service.search_with_fallback(
            query_vector=query_embedding,
            department=department,
        )
        
        if not retrieved_docs:
            warnings.append("관련 문서를 찾을 수 없습니다. 일반적인 답변만 제공됩니다.")
            logger.warning(
                "no_documents_found",
                trace_id=trace_id,
                department=department.value,
            )
        
        # 4. 답변 생성
        try:
            answer, confidence = await self._generate_answer(
                question=question,
                department=department,
                retrieved_docs=retrieved_docs,
                patient_info=patient_info,
            )
        except Exception as e:
            logger.error(
                "answer_generation_error",
                trace_id=trace_id,
                error=str(e),
            )
            raise
        
        # 5. 안전성 체크 및 경고 추가
        safety_warnings = self._check_safety(question, answer, department)
        warnings.extend(safety_warnings)
        
        # 응답 시간 계산
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 참조 문서 변환
        references = [
            DocumentReference(
                doc_id=doc["doc_id"],
                title=doc.get("title"),
                content=doc["content"][:500],  # 내용은 500자로 제한
                score=doc["score"],
                source=doc.get("source"),
                metadata=doc.get("metadata", {}),
            )
            for doc in retrieved_docs
        ]
        
        # 6. 로그 저장
        await self._save_attempt_log(
            trace_id=trace_id,
            question=question,
            department=department,
            answer=answer,
            references=retrieved_docs,
            latency_ms=latency_ms,
        )
        
        # 결과 반환
        result = {
            "trace_id": trace_id,
            "question": question,
            "department": department.value,
            "answer": answer,
            "references": [ref.dict() for ref in references],
            "confidence": confidence,
            "warnings": warnings,
            "meta": {
                "model": self.settings.openai.model,
                "prompt_version": self.prompt_builder.get_prompt_version(),
                "latency_ms": latency_ms,
                "documents_retrieved": len(retrieved_docs),
                "avg_doc_score": sum(d["score"] for d in retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0,
            }
        }
        
        logger.info(
            "rag_completed",
            trace_id=trace_id,
            department=department.value,
            docs_count=len(retrieved_docs),
            latency_ms=latency_ms,
        )
        
        return result
    
    async def _generate_answer(
        self,
        question: str,
        department: DepartmentCode,
        retrieved_docs: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, Optional[float]]:
        """
        RAG 기반 답변 생성
        
        Args:
            question: 질문
            department: 진료과
            retrieved_docs: 검색된 문서
            patient_info: 환자 정보
            
        Returns:
            (답변, 신뢰도)
        """
        # 프롬프트 구성
        messages = self.prompt_builder.build_rag_prompt(
            question=question,
            department=department,
            retrieved_docs=retrieved_docs,
        )
        
        # 환자 정보가 있으면 추가
        if patient_info:
            patient_context = self._format_patient_info(patient_info)
            messages.append({
                "role": "system",
                "content": f"환자 정보: {patient_context}"
            })
        
        # LLM 호출
        result = await self.llm_service.generate_completion(messages)
        
        answer = result["content"]
        
        # 신뢰도 계산 (문서 점수 기반)
        confidence = None
        if retrieved_docs:
            avg_score = sum(d["score"] for d in retrieved_docs) / len(retrieved_docs)
            confidence = min(avg_score, 1.0)
        
        return answer, confidence
    
    @staticmethod
    def _format_patient_info(patient_info: Dict[str, Any]) -> str:
        """
        환자 정보 포맷팅
        
        Args:
            patient_info: 환자 정보
            
        Returns:
            포맷된 문자열
        """
        info_parts = []
        
        if "age" in patient_info:
            info_parts.append(f"나이 {patient_info['age']}세")
        
        if "gender" in patient_info:
            gender_map = {"male": "남성", "female": "여성", "m": "남성", "f": "여성"}
            gender = gender_map.get(patient_info["gender"].lower(), patient_info["gender"])
            info_parts.append(gender)
        
        if "conditions" in patient_info:
            conditions = ", ".join(patient_info["conditions"])
            info_parts.append(f"기저질환: {conditions}")
        
        return ", ".join(info_parts)
    
    def _check_safety(
        self,
        question: str,
        answer: str,
        department: DepartmentCode
    ) -> List[str]:
        """
        안전성 체크 및 경고 생성
        
        Args:
            question: 질문
            answer: 답변
            department: 진료과
            
        Returns:
            경고 메시지 리스트
        """
        warnings = []
        
        # 응급 상황 경고
        from app.utils import EmergencyDetector
        if EmergencyDetector.has_emergency_signal(question):
            warnings.append("⚠️ 응급 상황이 의심됩니다. 즉시 119에 연락하거나 가까운 응급실을 방문하세요.")
        
        # 진단/처방 관련 경고
        diagnosis_keywords = ["진단", "처방", "약물", "수술"]
        if any(kw in answer for kw in diagnosis_keywords):
            warnings.append("본 답변은 참고용이며, 정확한 진단과 처방은 의료기관을 방문하여 받으시기 바랍니다.")
        
        # 산부인과 특별 경고
        if department == DepartmentCode.OBGYN:
            if "임신" in question or "태아" in question:
                warnings.append("임신 관련 사항은 반드시 산부인과 전문의와 상담하시기 바랍니다.")
        
        # 소아청소년과 특별 경고
        if department == DepartmentCode.PED:
            warnings.append("영유아 및 소아의 경우 증상이 급격히 악화될 수 있으니 주의 깊게 관찰하세요.")
        
        return warnings
    
    async def _save_attempt_log(
        self,
        trace_id: str,
        question: str,
        department: DepartmentCode,
        answer: str,
        references: List[Dict[str, Any]],
        latency_ms: int,
    ):
        """
        RAG 시도 로그 저장
        
        Args:
            trace_id: 추적 ID
            question: 질문
            department: 진료과
            answer: 답변
            references: 참조 문서
            latency_ms: 응답 시간
        """
        try:
            await self.audit_repository.create_rag_log(
                question=question,
                department=department.value,
                answer=answer,
                references=references,
                model=self.settings.openai.model,
                prompt_version=self.prompt_builder.get_prompt_version(),
                latency_ms=latency_ms,
                trace_id=trace_id,
            )
        except Exception as e:
            logger.error(
                "save_rag_log_error",
                trace_id=trace_id,
                error=str(e),
            )
