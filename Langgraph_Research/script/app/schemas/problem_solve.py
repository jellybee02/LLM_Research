from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.common import Meta

class ProblemSolveRequest(BaseModel):
    problem: str = Field(..., min_length=1)
    choices: Optional[List[str]] = None
    constraints: Optional[str] = None
    show_steps: bool = False

class ProblemSolveResponse(BaseModel):
    final_answer: str
    explanation: Optional[str] = None
    meta: Meta = Meta()
