from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.common import Meta

class ExpertQARequest(BaseModel):
    question: str = Field(..., min_length=1)
    domain: Optional[str] = None
    context: Optional[str] = None
    top_k: int = Field(default=3, ge=0, le=20)

class Source(BaseModel):
    title: str
    snippet: str
    uri: Optional[str] = None

class ExpertQAResponse(BaseModel):
    answer: str
    domain: str
    sources: List[Source] = []
    meta: Meta = Meta()
