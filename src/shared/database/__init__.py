"""
Database Module
Provides SQLAlchemy base, session management, and mixins
"""

from .base import (
    Base,
    db_transaction,
    db_readonly_session,
    get_session,
    execute_in_transaction,
    execute_readonly,
)
from .mixins import (
    TimestampMixin,
    UpdateTimestampMixin,
    SerializerMixin,
    ReprMixin,
    SoftDeleteMixin,
    VersionMixin,
    AuditMixin,
    UUIDMixin,
    NameMixin,
    StatusMixin,
)

__all__ = [
    # Base and session management
    "Base",
    "db_transaction",
    "db_readonly_session",
    "get_session",
    "execute_in_transaction",
    "execute_readonly",
    # Mixins
    "TimestampMixin",
    "UpdateTimestampMixin",
    "SerializerMixin",
    "ReprMixin",
    "SoftDeleteMixin",
    "VersionMixin",
    "AuditMixin",
    "UUIDMixin",
    "NameMixin",
    "StatusMixin",
]
