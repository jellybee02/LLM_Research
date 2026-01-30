"""
LLM Service
OpenAI API 호출 및 응답 처리
"""

import time
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI, OpenAIError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import Settings
from app.utils import get_logger

logger = get_logger(__name__)


class LLMService:
    """
    OpenAI LLM 서비스
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.openai.api_key,
            timeout=settings.openai.request_timeout,
            max_retries=settings.openai.max_retries,
        )
        self.model = settings.openai.model
        self.embedding_model = settings.openai.embedding_model
        self.temperature = settings.openai.temperature
        self.max_tokens = settings.openai.max_tokens
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        채팅 완성 생성
        
        Args:
            messages: OpenAI messages 형식
            temperature: 온도 (None이면 기본값 사용)
            max_tokens: 최대 토큰 (None이면 기본값 사용)
            
        Returns:
            {
                "content": 생성된 텍스트,
                "model": 모델명,
                "tokens": 사용된 토큰 수,
                "latency_ms": 응답 시간(밀리초)
            }
        """
        start_time = time.time()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            logger.info(
                "llm_completion_success",
                model=self.model,
                tokens=tokens_used,
                latency_ms=latency_ms
            )
            
            return {
                "content": content,
                "model": self.model,
                "tokens": tokens_used,
                "latency_ms": latency_ms,
            }
        
        except OpenAIError as e:
            logger.error(
                "llm_completion_error",
                error=str(e),
                model=self.model,
            )
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """
        텍스트 임베딩 생성
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            임베딩 벡터
        """
        start_time = time.time()
        
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            embedding = response.data[0].embedding
            
            logger.info(
                "embedding_success",
                model=self.embedding_model,
                text_length=len(text),
                latency_ms=latency_ms
            )
            
            return embedding
        
        except OpenAIError as e:
            logger.error(
                "embedding_error",
                error=str(e),
                model=self.embedding_model,
            )
            raise
    
    async def parse_structured_output(
        self,
        messages: List[Dict[str, str]],
        expected_format: str = "single_word"
    ) -> str:
        """
        구조화된 출력 파싱
        (예: 진료과 분류 결과 "EM", "IM" 등)
        
        Args:
            messages: OpenAI messages
            expected_format: 예상 출력 형식
            
        Returns:
            파싱된 결과
        """
        result = await self.generate_completion(
            messages=messages,
            temperature=0.0,  # 결정론적 출력
            max_tokens=50,  # 짧은 출력
        )
        
        content = result["content"].strip().upper()
        
        # 단일 단어 추출 (진료과 코드 등)
        if expected_format == "single_word":
            # 첫 번째 단어만 추출
            content = content.split()[0] if content.split() else content
        
        return content
