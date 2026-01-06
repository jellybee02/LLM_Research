from pydantic import BaseModel, Field

class ExpertRequest(BaseModel):
    question: str = Field(..., min_length=1)

class ExpertResponse(BaseModel):
    answer: str
