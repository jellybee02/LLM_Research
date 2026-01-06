from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router

def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
    )
    app.include_router(api_router, prefix=settings.API_PREFIX)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app

app = create_app()