from fastapi import APIRouter
from app.api.routes.expert import router as expert_router
from app.api.routes.qa_rag import router as qa_router

api_router = APIRouter()
api_router.include_router(expert_router, prefix="/expert", tags=["expert"])
api_router.include_router(qa_router, prefix="/qa", tags=["qa-rag"])