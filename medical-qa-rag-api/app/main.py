"""
FastAPI Main Application
의료 QA/RAG API 서버
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import get_settings
from app.api.routes import health_router, qa_router, rag_router
from app.utils import setup_logging, get_logger, generate_trace_id

# 설정 로드
settings = get_settings()

# 로깅 설정
setup_logging(settings)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리
    """
    # 시작 시
    logger.info(
        "application_startup",
        environment=settings.environment,
        version="1.0.0",
    )
    
    yield
    
    # 종료 시
    logger.info("application_shutdown")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Medical QA/RAG API",
    description="""
    의료 데이터 기반 QA 및 RAG 시스템
    
    ## 주요 기능
    
    ### 기능 1: QA 답변 생성 및 채점
    - 문제에 대한 정답 생성
    - 정답과의 비교 및 채점
    - 객관식/주관식 지원
    
    ### 기능 2: RAG 기반 전문 답변
    - 질문을 진료과로 자동 분류
    - 관련 의료 문서 검색
    - 근거 기반 전문 답변 생성
    - 안전성 체크 및 경고
    
    ## 진료과 분류
    - **EM**: 응급의학과 (Emergency Medicine)
    - **IM**: 내과 (Internal Medicine)
    - **PED**: 소아청소년과 (Pediatrics)
    - **OBGYN**: 산부인과 (Obstetrics & Gynecology)
    - **COMMON**: 공용 (General)
    
    ## 주의사항
    본 서비스는 참고용이며, 정확한 진단과 처방은 의료기관을 방문하여 받으시기 바랍니다.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 전역 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    전역 예외 처리
    """
    trace_id = generate_trace_id()
    
    logger.error(
        "unhandled_exception",
        trace_id=trace_id,
        path=request.url.path,
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "trace_id": trace_id,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "서버 내부 오류가 발생했습니다",
                "detail": str(exc) if settings.environment == "development" else None,
            }
        }
    )


# 라우터 등록
app.include_router(health_router)
app.include_router(qa_router, prefix="/api/v1")
app.include_router(rag_router, prefix="/api/v1")


@app.get("/")
async def root():
    """
    루트 엔드포인트
    """
    return {
        "service": "Medical QA/RAG API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        workers=1 if settings.server.reload else settings.server.workers,
        log_level=settings.logging.level.lower(),
    )
