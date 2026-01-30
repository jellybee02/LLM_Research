"""
Models Module
"""

from .schemas import (
    DepartmentCode,
    QuestionType,
    QARequest,
    QAResponse,
    RAGRequest,
    RAGResponse,
    DocumentReference,
    ErrorResponse,
    ErrorDetail,
    HealthResponse,
)

from .db_models import (
    Base,
    QAMaster,
    QAAttemptLog,
    RAGAttemptLog,
    AuditLog,
)

__all__ = [
    # Enums
    "DepartmentCode",
    "QuestionType",
    # Request/Response Schemas
    "QARequest",
    "QAResponse",
    "RAGRequest",
    "RAGResponse",
    "DocumentReference",
    "ErrorResponse",
    "ErrorDetail",
    "HealthResponse",
    # Database Models
    "Base",
    "QAMaster",
    "QAAttemptLog",
    "RAGAttemptLog",
    "AuditLog",
]
