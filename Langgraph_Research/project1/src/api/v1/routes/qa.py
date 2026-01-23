from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/qa", tags=["qa"])


class SolveRequest(BaseModel):
    question: str = Field(..., description="문제 텍스트(보기 포함 가능)")


class SolveResponse(BaseModel):
    answer: str


@router.post("/solve", response_model=SolveResponse, summary="문제 풀이(정답 반환)")
def solve(req: SolveRequest):
    # TODO: services.qa_service 로직 호출로 교체
    dummy_answer = "(dummy) 정답: 아직 연결 안됨"
    return SolveResponse(answer=dummy_answer)


