from fastapi import APIRouter
from app.api.v1.endpoints.expert_qa import router as expert_qa_router
from app.api.v1.endpoints.problem_solve import router as problem_solve_router

api_router = APIRouter()
api_router.include_router(expert_qa_router, prefix="/expert", tags=["expert"])
api_router.include_router(problem_solve_router, prefix="/problem", tags=["problem"])