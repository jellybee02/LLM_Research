from fastapi import APIRouter

from src.api.v1.routes.health import router as health_router
# 앞으로 추가될 것들 예시:
# from src.api.v1.routes.rag import router as rag_router
# from src.api.v1.routes.qa import router as qa_router

base_path = "/api/v1"


api_v1_router = APIRouter(prefix=base_path)

# 라우터들을 v1 하위로 묶어 등록
api_v1_router.include_router(health_router, tags=["health"])
# api_v1_router.include_router(rag_router, prefix="/rag", tags=["rag"])
# api_v1_router.include_router(qa_router, prefix="/qa", tags=["qa"])