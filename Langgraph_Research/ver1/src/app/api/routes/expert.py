from fastapi import APIRouter, Depends
from app.schemas.expert import ExpertRequest, ExpertResponse
from app.services.llm import get_llm_client, LLMClient

router = APIRouter()

@router.post("/answer", response_model=ExpertResponse)
def answer(req: ExpertRequest, llm: LLMClient = Depends(get_llm_client)):
    system = "너는 사용자의 질문에 대해 전문적으로 답변하는 도우미다. 근거와 한계를 명확히 설명해라."
    answer = llm.invoke(system_prompt=system, user_text=req.question)
    return ExpertResponse(answer=answer)
''