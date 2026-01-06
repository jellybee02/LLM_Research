from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class Meta(BaseModel):
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    usage: Usage = Field(default_factory=Usage)
    extra: Dict[str, Any] = Field(default_factory=dict)
