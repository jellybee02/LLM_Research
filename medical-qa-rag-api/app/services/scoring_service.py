"""
Scoring Service
QA 답변 채점 서비스
"""

from typing import Dict, Any, Optional
from difflib import SequenceMatcher

from app.config import Settings
from app.utils import get_logger

logger = get_logger(__name__)


class ScoringService:
    """
    답변 채점 서비스
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.exact_match_threshold = settings.scoring.exact_match_threshold
        self.similarity_threshold = settings.scoring.similarity_threshold
        self.use_llm_judge = settings.scoring.use_llm_judge
    
    def score_answer(
        self,
        predicted: str,
        correct: str,
        q_type: str = "short_answer"
    ) -> Dict[str, Any]:
        """
        답변 채점
        
        Args:
            predicted: 모델 예측 답변
            correct: 정답
            q_type: 문제 유형
            
        Returns:
            {
                "is_correct": bool,
                "score": float (0.0 ~ 1.0),
                "explanation": str
            }
        """
        # 정규화
        pred_normalized = self._normalize_answer(predicted)
        correct_normalized = self._normalize_answer(correct)
        
        # 객관식 (선택지 번호 매칭)
        if q_type == "multiple_choice":
            return self._score_multiple_choice(pred_normalized, correct_normalized)
        
        # 주관식 (유사도 기반)
        return self._score_short_answer(pred_normalized, correct_normalized)
    
    def _score_multiple_choice(
        self,
        predicted: str,
        correct: str
    ) -> Dict[str, Any]:
        """
        객관식 답변 채점
        선택지 번호 완전 일치 확인
        
        Args:
            predicted: 예측 답변 (정규화됨)
            correct: 정답 (정규화됨)
            
        Returns:
            채점 결과
        """
        # 선택지 번호 추출 (1, 2, 3 등)
        pred_number = self._extract_choice_number(predicted)
        correct_number = self._extract_choice_number(correct)
        
        is_correct = pred_number == correct_number and pred_number is not None
        score = 1.0 if is_correct else 0.0
        
        explanation = (
            f"선택지 일치 (정답: {correct_number}, 예측: {pred_number})"
            if is_correct
            else f"선택지 불일치 (정답: {correct_number}, 예측: {pred_number})"
        )
        
        logger.info(
            "multiple_choice_scored",
            is_correct=is_correct,
            correct_number=correct_number,
            pred_number=pred_number,
        )
        
        return {
            "is_correct": is_correct,
            "score": score,
            "explanation": explanation,
        }
    
    def _score_short_answer(
        self,
        predicted: str,
        correct: str
    ) -> Dict[str, Any]:
        """
        주관식 답변 채점
        문자열 유사도 기반
        
        Args:
            predicted: 예측 답변 (정규화됨)
            correct: 정답 (정규화됨)
            
        Returns:
            채점 결과
        """
        # 완전 일치 확인
        if predicted == correct:
            return {
                "is_correct": True,
                "score": 1.0,
                "explanation": "정답과 완전히 일치",
            }
        
        # 유사도 계산
        similarity = self._calculate_similarity(predicted, correct)
        
        # 임계값 기반 판단
        is_correct = similarity >= self.exact_match_threshold
        
        if similarity >= self.exact_match_threshold:
            explanation = f"정답과 매우 유사 (유사도: {similarity:.2f})"
        elif similarity >= self.similarity_threshold:
            explanation = f"부분 정답 (유사도: {similarity:.2f})"
        else:
            explanation = f"오답 (유사도: {similarity:.2f})"
        
        logger.info(
            "short_answer_scored",
            is_correct=is_correct,
            similarity=similarity,
        )
        
        return {
            "is_correct": is_correct,
            "score": similarity,
            "explanation": explanation,
        }
    
    @staticmethod
    def _normalize_answer(text: str) -> str:
        """
        답변 정규화
        - 소문자 변환
        - 공백 정리
        - 특수문자 제거
        
        Args:
            text: 원본 텍스트
            
        Returns:
            정규화된 텍스트
        """
        if not text:
            return ""
        
        # 소문자 변환
        text = text.lower()
        
        # 공백 정리
        text = " ".join(text.split())
        
        # 특수문자 제거 (숫자와 한글, 영문만 유지)
        import re
        text = re.sub(r'[^a-z0-9가-힣\s]', '', text)
        
        return text.strip()
    
    @staticmethod
    def _extract_choice_number(text: str) -> Optional[int]:
        """
        선택지 번호 추출
        "1", "1번", "①" 등에서 숫자 추출
        
        Args:
            text: 답변 텍스트
            
        Returns:
            선택지 번호 (1, 2, 3...) 또는 None
        """
        import re
        
        # 숫자만 추출
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
        
        # 동그라미 숫자 (①, ②, ③...)
        circle_numbers = {'①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5}
        for symbol, number in circle_numbers.items():
            if symbol in text:
                return number
        
        return None
    
    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """
        두 텍스트의 유사도 계산
        SequenceMatcher 사용
        
        Args:
            text1: 텍스트 1
            text2: 텍스트 2
            
        Returns:
            유사도 (0.0 ~ 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        return SequenceMatcher(None, text1, text2).ratio()
    
    def score_with_partial_credit(
        self,
        predicted: str,
        correct: str,
        keywords: list[str]
    ) -> Dict[str, Any]:
        """
        키워드 기반 부분 점수 채점
        의료 용어 등 핵심 키워드 포함 여부로 점수 부여
        
        Args:
            predicted: 예측 답변
            correct: 정답
            keywords: 핵심 키워드 리스트
            
        Returns:
            채점 결과
        """
        pred_normalized = self._normalize_answer(predicted)
        
        # 키워드 매칭 점수
        matched_keywords = [
            kw for kw in keywords
            if self._normalize_answer(kw) in pred_normalized
        ]
        
        keyword_score = len(matched_keywords) / len(keywords) if keywords else 0.0
        
        # 유사도 점수
        similarity_score = self._calculate_similarity(
            pred_normalized,
            self._normalize_answer(correct)
        )
        
        # 최종 점수 (키워드 70%, 유사도 30%)
        final_score = keyword_score * 0.7 + similarity_score * 0.3
        
        is_correct = final_score >= self.exact_match_threshold
        
        explanation = (
            f"키워드 매칭: {len(matched_keywords)}/{len(keywords)} "
            f"(점수: {final_score:.2f})"
        )
        
        return {
            "is_correct": is_correct,
            "score": final_score,
            "explanation": explanation,
            "matched_keywords": matched_keywords,
        }
