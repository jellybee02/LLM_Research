"""
Security Utilities
PII 마스킹, 데이터 보안 관련 유틸리티
"""

import re
from typing import Any, Dict, List


class PIIMasker:
    """
    개인 식별 정보(PII) 마스킹
    """
    
    def __init__(self, pii_fields: List[str]):
        """
        Args:
            pii_fields: 마스킹할 필드명 리스트
        """
        self.pii_fields = [field.lower() for field in pii_fields]
        
        # 정규표현식 패턴
        self.patterns = {
            "주민등록번호": re.compile(r'\d{6}-?\d{7}'),
            "전화번호": re.compile(r'01[0-9]-?\d{3,4}-?\d{4}'),
            "이메일": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            "신용카드": re.compile(r'\d{4}-?\d{4}-?\d{4}-?\d{4}'),
        }
    
    def mask_text(self, text: str) -> str:
        """
        텍스트 내 PII 마스킹
        
        Args:
            text: 원본 텍스트
            
        Returns:
            마스킹된 텍스트
        """
        if not text:
            return text
        
        masked_text = text
        
        # 각 패턴에 대해 마스킹 적용
        for pattern_name, pattern in self.patterns.items():
            masked_text = pattern.sub(self._mask_match, masked_text)
        
        return masked_text
    
    def mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        딕셔너리 내 PII 마스킹
        
        Args:
            data: 원본 딕셔너리
            
        Returns:
            마스킹된 딕셔너리
        """
        if not data:
            return data
        
        masked_data = {}
        
        for key, value in data.items():
            # PII 필드명이면 완전 마스킹
            if key.lower() in self.pii_fields:
                masked_data[key] = "***MASKED***"
            # 문자열이면 패턴 기반 마스킹
            elif isinstance(value, str):
                masked_data[key] = self.mask_text(value)
            # 딕셔너리면 재귀 호출
            elif isinstance(value, dict):
                masked_data[key] = self.mask_dict(value)
            # 리스트면 각 항목 처리
            elif isinstance(value, list):
                masked_data[key] = [
                    self.mask_dict(item) if isinstance(item, dict)
                    else self.mask_text(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                masked_data[key] = value
        
        return masked_data
    
    @staticmethod
    def _mask_match(match) -> str:
        """
        매칭된 텍스트 마스킹
        앞 2자리만 남기고 나머지 *로 변경
        """
        text = match.group()
        if len(text) <= 2:
            return "*" * len(text)
        return text[:2] + "*" * (len(text) - 2)


def sanitize_user_input(text: str, max_length: int = 10000) -> str:
    """
    사용자 입력 정제
    
    Args:
        text: 사용자 입력 텍스트
        max_length: 최대 길이
        
    Returns:
        정제된 텍스트
    """
    if not text:
        return ""
    
    # 길이 제한
    text = text[:max_length]
    
    # 제어 문자 제거 (줄바꿈, 탭은 유지)
    text = "".join(char for char in text if char.isprintable() or char in ['\n', '\r', '\t'])
    
    # 연속된 공백 정리
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def anonymize_ip(ip_address: str) -> str:
    """
    IP 주소 익명화
    마지막 옥텟을 0으로 변경
    
    Args:
        ip_address: 원본 IP 주소
        
    Returns:
        익명화된 IP 주소
    """
    if not ip_address:
        return ""
    
    # IPv4
    if "." in ip_address:
        parts = ip_address.split(".")
        if len(parts) == 4:
            return ".".join(parts[:3] + ["0"])
    
    # IPv6 (간단한 처리)
    if ":" in ip_address:
        parts = ip_address.split(":")
        if len(parts) > 4:
            return ":".join(parts[:4] + ["0000"] * (len(parts) - 4))
    
    return ip_address


def generate_anonymous_user_id(user_identifier: str) -> str:
    """
    사용자 식별자를 익명화된 ID로 변환
    
    Args:
        user_identifier: 원본 사용자 식별자
        
    Returns:
        익명화된 사용자 ID
    """
    import hashlib
    
    if not user_identifier:
        return ""
    
    # SHA-256 해시의 앞 16자리 사용
    hash_obj = hashlib.sha256(user_identifier.encode('utf-8'))
    return f"user_{hash_obj.hexdigest()[:16]}"
