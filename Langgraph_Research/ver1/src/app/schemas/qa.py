from pydantic import BaseModel, Field
from typing import Optional, List

class QaRequest(BaseModel):
    problem: str = Field(..., min_length=1)
    # 선택: 문제 유형/과목/난이도 등
    category: Optional[str] = None

class RetrievedChunk(BaseModel):
    content: str
    source: Optional[str] = None
    score: Optional[float] = None

class QaResponse(BaseModel):
    answer: str
    retrieved: List[RetrievedChunk] = []
