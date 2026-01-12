from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/rag", tags=["rag"])


class RagAskRequest(BaseModel):
    question: str = Field(..., description="사용자 질문")


class RagAskResponse(BaseModel):
    answer: str


@router.post("/ask", response_model=RagAskResponse, summary="RAG 기반 전문 답변")
def ask(req: RagAskRequest):
    # TODO: services.rag_service 로직 호출로 교체
    dummy_answer = f"(dummy) 질문: {req.question}"
    return RagAskResponse(answer=dummy_answer)
