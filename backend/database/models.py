"""
SQLAlchemy models for WebScan Pro.
Defines ScanSession and Vulnerability tables.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def generate_uuid() -> str:
    """Generate a UUID4 string."""
    return str(uuid.uuid4())


class ScanSession(Base):
    """Represents a single scan session with a target URL."""

    __tablename__ = "scan_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True
    )  # pending, running, completed, failed
    scan_type: Mapped[str] = mapped_column(
        String(20), default="full"
    )  # full, passive, active
    security_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="en")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scan_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationship to vulnerabilities
    vulnerabilities = relationship(
        "Vulnerability", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ScanSession(id={self.id}, target={self.target_url}, status={self.status})>"


class Vulnerability(Base):
    """Represents a single vulnerability found during a scan."""

    __tablename__ = "vulnerabilities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scan_sessions.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # sql_injection, xss, ssl, headers, cookies, traversal, info_disclosure
    severity: Mapped[str] = mapped_column(
        String(10), nullable=False, default="medium"
    )  # critical, high, medium, low, info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    parameter: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cvss_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationship back to session
    session = relationship("ScanSession", back_populates="vulnerabilities")

    def __repr__(self) -> str:
        return (
            f"<Vulnerability(id={self.id}, type={self.type}, severity={self.severity})>"
        )
