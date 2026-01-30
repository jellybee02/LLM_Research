from fastapi import APIRouter
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.items import router as items_router

api_v1_router = APIRouter()
api_v1_router.include_router(users_router, prefix="/users", tags=["users"])
api_v1_router.include_router(items_router, prefix="/items", tags=["items"])
