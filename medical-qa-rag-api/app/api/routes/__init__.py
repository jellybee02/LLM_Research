"""
API Routes Module
"""

from .health import router as health_router
from .qa import router as qa_router
from .rag import router as rag_router

__all__ = [
    "health_router",
    "qa_router",
    "rag_router",
]
