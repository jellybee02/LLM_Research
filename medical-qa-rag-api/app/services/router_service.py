"""
Router Service
질문을 진료과로 분류하는 서비스
"""

from typing import Optional

from app.config import Settings
from app.models import DepartmentCode
from app.services.llm_service import LLMService
from app.utils import get_logger, PromptBuilder, EmergencyDetector, DepartmentKeywordRouter

logger = get_logger(__name__)


class RouterService:
    """
    진료과 라우팅 서비스
    """
    
    def __init__(self, settings: Settings, llm_service: LLMService):
        self.settings = settings
        self.llm_service = llm_service
        self.prompt_builder = PromptBuilder(settings)
    
    async def route_question(
        self,
        question: str,
        use_llm: bool = True,
    ) -> DepartmentCode:
        """
        질문을 진료과로 분류
        
        우선순위:
        1. 응급 키워드 체크 → EM
        2. 키워드 기반 제안
        3. LLM 기반 분류
        4. 기본값: COMMON
        
        Args:
            question: 사용자 질문
            use_llm: LLM 사용 여부
            
        Returns:
            분류된 진료과 코드
        """
        # 1단계: 응급 상황 감지
        if EmergencyDetector.has_emergency_signal(question):
            logger.info(
                "emergency_detected",
                question_preview=question[:100],
            )
            return DepartmentCode.EM
        
        # 2단계: 키워드 기반 제안
        keyword_dept = DepartmentKeywordRouter.suggest_department(question)
        if keyword_dept:
            logger.info(
                "keyword_routing",
                department=keyword_dept.value,
                question_preview=question[:100],
            )
            
            # 키워드 신뢰도가 높으면 LLM 생략 가능
            if not use_llm:
                return keyword_dept
        
        # 3단계: LLM 기반 분류
        if use_llm:
            try:
                llm_dept = await self._classify_with_llm(question)
                
                # LLM 결과가 유효하면 사용
                if llm_dept:
                    logger.info(
                        "llm_routing",
                        department=llm_dept.value,
                        keyword_suggestion=keyword_dept.value if keyword_dept else None,
                        question_preview=question[:100],
                    )
                    return llm_dept
            
            except Exception as e:
                logger.error(
                    "llm_routing_error",
                    error=str(e),
                    question_preview=question[:100],
                )
                # LLM 실패 시 키워드 결과 또는 COMMON 사용
        
        # 4단계: Fallback
        fallback_dept = keyword_dept or DepartmentCode.COMMON
        logger.info(
            "fallback_routing",
            department=fallback_dept.value,
            question_preview=question[:100],
        )
        return fallback_dept
    
    async def _classify_with_llm(self, question: str) -> Optional[DepartmentCode]:
        """
        LLM을 사용한 진료과 분류
        
        Args:
            question: 사용자 질문
            
        Returns:
            분류된 진료과 (실패 시 None)
        """
        messages = self.prompt_builder.build_router_prompt(question)
        
        # LLM 호출
        result = await self.llm_service.parse_structured_output(
            messages=messages,
            expected_format="single_word"
        )
        
        # 결과 검증 및 변환
        result = result.strip().upper()
        
        # 유효한 진료과 코드인지 확인
        try:
            department = DepartmentCode(result)
            return department
        except ValueError:
            logger.warning(
                "invalid_department_code",
                llm_output=result,
            )
            return None
    
    def validate_department(self, dept_code: str) -> Optional[DepartmentCode]:
        """
        진료과 코드 검증
        
        Args:
            dept_code: 진료과 코드 문자열
            
        Returns:
            유효한 DepartmentCode 또는 None
        """
        try:
            return DepartmentCode(dept_code.upper())
        except ValueError:
            return None
