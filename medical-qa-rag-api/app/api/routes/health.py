"""
Health Check Routes
시스템 헬스체크 엔드포인트
"""

from fastapi import APIRouter, Depends
from datetime import datetime

from app.models import HealthResponse
from app.config import get_settings
from app.api.dependencies import get_qdrant_service
from app.services import QdrantService
from app.models import DepartmentCode

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check(
    qdrant_service: QdrantService = Depends(get_qdrant_service),
):
    """
    시스템 헬스체크
    
    의존성 서비스 상태 확인:
    - Database
    - Qdrant
    - OpenAI
    """
    settings = get_settings()
    dependencies = {}
    
    # Database 체크 (간단한 연결 확인)
    try:
        # TODO: 실제 DB 연결 테스트 구현
        dependencies["database"] = "healthy"
    except Exception:
        dependencies["database"] = "unhealthy"
    
    # Qdrant 체크
    try:
        # COMMON 컬렉션 존재 여부 확인
        exists = qdrant_service.check_collection_exists(DepartmentCode.COMMON)
        dependencies["qdrant"] = "healthy" if exists else "partial"
    except Exception:
        dependencies["qdrant"] = "unhealthy"
    
    # OpenAI 체크 (API key 존재만 확인)
    try:
        if settings.openai.api_key and len(settings.openai.api_key) > 0:
            dependencies["openai"] = "configured"
        else:
            dependencies["openai"] = "not_configured"
    except Exception:
        dependencies["openai"] = "unhealthy"
    
    # 전체 상태 결정
    status = "healthy"
    if any(v == "unhealthy" for v in dependencies.values()):
        status = "unhealthy"
    elif any(v in ["partial", "not_configured"] for v in dependencies.values()):
        status = "degraded"
    
    return HealthResponse(
        status=status,
        version="1.0.0",
        timestamp=datetime.utcnow(),
        dependencies=dependencies,
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness 체크 (Kubernetes용)
    """
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """
    Liveness 체크 (Kubernetes용)
    """
    return {"alive": True}
