"""
Prompt Template Utilities
프롬프트 템플릿 관리 및 렌더링
"""

from typing import Dict, Any
from app.config import Settings
from app.models import DepartmentCode


class PromptBuilder:
    """
    프롬프트 빌더
    config.yaml의 프롬프트 템플릿을 활용
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.prompts = settings.prompts
    
    def build_qa_prompt(self, question: str) -> list[Dict[str, str]]:
        """
        QA 답변 생성용 프롬프트 구성
        
        Args:
            question: 문제 텍스트
            
        Returns:
            OpenAI messages 형식
        """
        system_prompt = self.prompts.qa_answering["system"]
        user_template = self.prompts.qa_answering["user_template"]
        
        user_prompt = user_template.format(question=question)
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def build_router_prompt(self, question: str) -> list[Dict[str, str]]:
        """
        진료과 분류용 프롬프트 구성
        
        Args:
            question: 사용자 질문
            
        Returns:
            OpenAI messages 형식
        """
        system_prompt = self.prompts.router["system"]
        user_template = self.prompts.router["user_template"]
        
        user_prompt = user_template.format(question=question)
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def build_rag_prompt(
        self,
        question: str,
        department: DepartmentCode,
        retrieved_docs: list[Dict[str, Any]]
    ) -> list[Dict[str, str]]:
        """
        RAG 답변 생성용 프롬프트 구성
        
        Args:
            question: 사용자 질문
            department: 진료과 코드
            retrieved_docs: 검색된 문서 목록
            
        Returns:
            OpenAI messages 형식
        """
        # 진료과별 시스템 프롬프트 선택
        dept_key = department.value.lower()
        system_prompt = self.prompts.rag.get(dept_key, {}).get("system", "")
        
        if not system_prompt:
            system_prompt = self.prompts.rag["common"]["system"]
        
        # 검색된 문서를 컨텍스트로 변환
        context = self._format_retrieved_docs(retrieved_docs)
        
        # 사용자 프롬프트 구성
        user_prompt = f"""질문: {question}

관련 의료 문서:
{context}

위 문서를 근거로 질문에 답변해주세요. 
반드시 사용한 문서의 출처를 명시하세요.
근거가 불충분하면 추가 정보가 필요함을 명시하거나 의료진 상담을 권고하세요."""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    @staticmethod
    def _format_retrieved_docs(docs: list[Dict[str, Any]]) -> str:
        """
        검색된 문서를 프롬프트용 텍스트로 포맷
        
        Args:
            docs: 검색된 문서 목록
            
        Returns:
            포맷된 컨텍스트 문자열
        """
        if not docs:
            return "관련 문서를 찾을 수 없습니다."
        
        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            doc_text = f"""
[문서 {i}]
출처: {doc.get('source', '알 수 없음')}
제목: {doc.get('title', '제목 없음')}
내용: {doc.get('content', '')}
관련도 점수: {doc.get('score', 0):.2f}
"""
            formatted_docs.append(doc_text.strip())
        
        return "\n\n".join(formatted_docs)
    
    def get_prompt_version(self) -> str:
        """현재 프롬프트 버전 반환"""
        return self.prompts.version


class EmergencyDetector:
    """
    응급 상황 감지
    특정 키워드가 있으면 응급의학과로 우선 라우팅
    """
    
    EMERGENCY_KEYWORDS = [
        # 흉부 관련
        "흉통", "가슴통증", "심장통증", "심근경색",
        # 호흡기
        "호흡곤란", "숨쉬기힘듦", "숨이막힘",
        # 신경계
        "의식저하", "의식불명", "정신혼미", "실신", "발작",
        # 출혈
        "심한출혈", "대량출혈", "피를많이흘림",
        # 외상
        "교통사고", "추락", "골절",
        # 기타 응급
        "쇼크", "중독", "질식",
    ]
    
    @classmethod
    def has_emergency_signal(cls, question: str) -> bool:
        """
        질문에 응급 신호가 있는지 확인
        
        Args:
            question: 사용자 질문
            
        Returns:
            응급 키워드 포함 여부
        """
        question_lower = question.lower().replace(" ", "")
        
        for keyword in cls.EMERGENCY_KEYWORDS:
            if keyword.replace(" ", "") in question_lower:
                return True
        
        return False


class DepartmentKeywordRouter:
    """
    키워드 기반 진료과 라우팅 보조
    LLM 분류 전 규칙 기반 사전 필터링
    """
    
    DEPARTMENT_KEYWORDS = {
        DepartmentCode.EM: [
            "응급", "급성", "심한통증", "즉시", "119",
        ] + EmergencyDetector.EMERGENCY_KEYWORDS,
        
        DepartmentCode.OBGYN: [
            "임신", "출산", "산후", "월경", "생리", "질출혈",
            "태아", "임산부", "수유", "산부인과",
        ],
        
        DepartmentCode.PED: [
            "영아", "유아", "신생아", "소아", "아기", "어린이",
            "청소년", "예방접종", "성장", "발달",
        ],
        
        DepartmentCode.IM: [
            "당뇨", "고혈압", "고지혈증", "만성질환",
            "소화기", "간", "위", "대장", "췌장",
            "약물", "복용", "처방",
        ],
    }
    
    @classmethod
    def suggest_department(cls, question: str) -> DepartmentCode | None:
        """
        키워드 기반 진료과 제안
        
        Args:
            question: 사용자 질문
            
        Returns:
            제안된 진료과 (없으면 None)
        """
        question_lower = question.lower().replace(" ", "")
        
        # 각 진료과별 키워드 매칭 점수 계산
        scores = {}
        for dept, keywords in cls.DEPARTMENT_KEYWORDS.items():
            score = sum(
                1 for keyword in keywords
                if keyword.replace(" ", "") in question_lower
            )
            if score > 0:
                scores[dept] = score
        
        if not scores:
            return None
        
        # 가장 높은 점수의 진료과 반환
        return max(scores, key=scores.get)
