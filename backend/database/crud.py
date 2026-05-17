"""
Async CRUD operations for WebScan Pro database.
Uses aiosqlite with SQLAlchemy async sessions.
"""

import logging
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload

from config import settings
from database.models import Base, ScanSession, Vulnerability

logger = logging.getLogger("webscanpro.db")

# Create async engine and session factory
async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize the database by creating all tables."""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    async with AsyncSessionLocal() as session:
        yield session


# ─── ScanSession CRUD ───────────────────────────────────────────────


async def create_scan_session(
    target_url: str,
    scan_type: str = "full",
    language: str = "en",
) -> ScanSession:
    """Create a new scan session in the database."""
    async with AsyncSessionLocal() as db:
        session = ScanSession(
            target_url=target_url,
            scan_type=scan_type,
            language=language,
            status="pending",
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        logger.info(f"Created scan session {session.id} for {target_url}")
        return session


async def get_scan_session(session_id: str) -> Optional[ScanSession]:
    """Get a scan session by ID with its vulnerabilities."""
    async with AsyncSessionLocal() as db:
        stmt = (
            select(ScanSession)
            .where(ScanSession.id == session_id)
            .options(selectinload(ScanSession.vulnerabilities))
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        return session


async def update_scan_status(
    session_id: str,
    status: str,
    security_score: Optional[float] = None,
    risk_level: Optional[str] = None,
    ai_summary: Optional[str] = None,
    scan_metadata: Optional[dict] = None,
    error_message: Optional[str] = None,
) -> Optional[ScanSession]:
    """Update the status and results of a scan session."""
    async with AsyncSessionLocal() as db:
        stmt = select(ScanSession).where(ScanSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            logger.warning(f"Scan session {session_id} not found for update.")
            return None

        session.status = status
        session.updated_at = datetime.now(timezone.utc)

        if security_score is not None:
            session.security_score = security_score
        if risk_level is not None:
            session.risk_level = risk_level
        if ai_summary is not None:
            session.ai_summary = ai_summary
        if scan_metadata is not None:
            session.scan_metadata = scan_metadata
        if error_message is not None:
            session.error_message = error_message

        await db.commit()
        await db.refresh(session)
        return session


async def get_scan_history(limit: int = 20, offset: int = 0) -> List[ScanSession]:
    """Get the scan history ordered by creation date descending."""
    async with AsyncSessionLocal() as db:
        stmt = (
            select(ScanSession)
            .options(selectinload(ScanSession.vulnerabilities))
            .order_by(ScanSession.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        return list(sessions)


async def delete_scan_session(session_id: str) -> bool:
    """Delete a scan session and its associated vulnerabilities."""
    async with AsyncSessionLocal() as db:
        stmt = select(ScanSession).where(ScanSession.id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return False

        await db.delete(session)
        await db.commit()
        logger.info(f"Deleted scan session {session_id}")
        return True


# ─── Vulnerability CRUD ─────────────────────────────────────────────


async def add_vulnerability(
    session_id: str,
    vuln_type: str,
    severity: str,
    title: str,
    description: Optional[str] = None,
    url: Optional[str] = None,
    parameter: Optional[str] = None,
    payload: Optional[str] = None,
    evidence: Optional[str] = None,
    remediation: Optional[str] = None,
    cvss_score: Optional[float] = None,
) -> Vulnerability:
    """Add a vulnerability to a scan session."""
    async with AsyncSessionLocal() as db:
        vuln = Vulnerability(
            session_id=session_id,
            type=vuln_type,
            severity=severity,
            title=title,
            description=description,
            url=url,
            parameter=parameter,
            payload=payload,
            evidence=evidence,
            remediation=remediation,
            cvss_score=cvss_score,
        )
        db.add(vuln)
        await db.commit()
        await db.refresh(vuln)
        return vuln


async def get_vulnerabilities(
    session_id: str,
    severity: Optional[str] = None,
    vuln_type: Optional[str] = None,
) -> List[Vulnerability]:
    """Get vulnerabilities for a session, optionally filtered by severity or type."""
    async with AsyncSessionLocal() as db:
        stmt = select(Vulnerability).where(Vulnerability.session_id == session_id)

        if severity:
            stmt = stmt.where(Vulnerability.severity == severity)
        if vuln_type:
            stmt = stmt.where(Vulnerability.type == vuln_type)

        stmt = stmt.order_by(Vulnerability.discovered_at.asc())
        result = await db.execute(stmt)
        vulns = result.scalars().all()
        return list(vulns)


async def delete_vulnerabilities(session_id: str) -> int:
    """Delete all vulnerabilities for a session. Returns count deleted."""
    async with AsyncSessionLocal() as db:
        stmt = delete(Vulnerability).where(Vulnerability.session_id == session_id)
        result = await db.execute(stmt)
        await db.commit()
        count = result.rowcount if result.rowcount is not None else 0
        logger.info(f"Deleted {count} vulnerabilities for session {session_id}")
        return count
