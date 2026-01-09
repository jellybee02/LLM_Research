from fastapi import FastAPI

from src.api.v1.router import api_v1_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="My FastAPI",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # v1 라우터 등록
    app.include_router(api_v1_router)

    return app


app = create_app()