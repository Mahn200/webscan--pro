"""
WebScan Pro Backend - FastAPI Application
AI-Powered Cybersecurity & Vulnerability Scanning Tool
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import settings
from database.crud import (
    add_vulnerability,
    create_scan_session,
    delete_scan_session,
    get_scan_history,
    get_scan_session,
    init_db,
    update_scan_status,
)
from ai.deepseek_client import deepseek_client
from reports.pdf_generator import generate_pdf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("webscanpro")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    logger.info("WebScan Pro Backend starting up...")
    logger.info(f"API configured on {settings.api_host}:{settings.api_port}")

    # Initialize database on startup
    await init_db()

    yield
    logger.info("WebScan Pro Backend shutting down...")


app = FastAPI(
    title="WebScan Pro API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for fonts and assets
try:
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")
except Exception as e:
    logger.warning(f"Could not mount assets directory: {e}")


# ─── Runtime Settings Override ─────────────────────────────────────

# In-memory override store (resets on backend restart — Flutter re-syncs on startup)
_runtime_settings: dict = {}


class RuntimeSettings(BaseModel):
    deepseek_api_key: Optional[str] = None
    deepseek_model: Optional[str] = None
    scan_timeout: Optional[int] = None
    max_retries: Optional[int] = None
    waf_evasion: Optional[bool] = None
    stealth_mode: Optional[bool] = None


@app.post("/settings/update")
async def update_settings(payload: RuntimeSettings):
    """Receive runtime settings from the Flutter frontend."""
    global _runtime_settings
    data = payload.model_dump(exclude_none=True)
    _runtime_settings.update(data)

    # Propagate API key and model to the DeepSeek singleton
    if "deepseek_api_key" in data or "deepseek_model" in data:
        deepseek_client.reconfigure(
            api_key=data.get("deepseek_api_key"),
            model=data.get("deepseek_model"),
        )

    # Never log the API key value — only log the key names
    logger.info(f"Runtime settings updated: {list(data.keys())}")
    return {"status": "ok", "updated": list(data.keys())}


@app.get("/settings/current")
async def get_current_settings():
    """Return effective settings (runtime overrides with .env fallbacks).
    NEVER returns the API key value."""
    return {
        "scan_timeout": _runtime_settings.get("scan_timeout", settings.scan_timeout),
        "max_retries": _runtime_settings.get("max_retries", settings.max_retries),
        "deepseek_model": _runtime_settings.get(
            "deepseek_model", settings.deepseek_model
        ),
        "waf_evasion": _runtime_settings.get("waf_evasion", True),
        "stealth_mode": _runtime_settings.get("stealth_mode", True),
    }


# ─── Pydantic Models ───────────────────────────────────────────────


class ScanStartRequest(BaseModel):
    target_url: str
    scan_type: str = "full"
    language: str = "en"


class ScanStatusResponse(BaseModel):
    id: str
    target_url: str
    status: str
    progress: float = 0.0


class VulnerabilityResponse(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    parameter: Optional[str] = None
    payload: Optional[str] = None
    evidence: Optional[str] = None
    remediation: Optional[str] = None
    cvss_score: Optional[float] = None


class ScanResultResponse(BaseModel):
    id: str
    target_url: str
    status: str
    scan_type: str
    security_score: Optional[float] = None
    risk_level: Optional[str] = None
    ai_summary: Optional[str] = None
    vulnerabilities: List[VulnerabilityResponse] = []
    created_at: str
    language: str


class HistoryItem(BaseModel):
    id: str
    target_url: str
    status: str
    security_score: Optional[float] = None
    risk_level: Optional[str] = None
    vulnerability_count: int = 0
    created_at: str


# ─── Health Check ──────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "ok", "service": "WebScan Pro Backend", "version": "2.0.0"}


# ─── Scan Endpoints ────────────────────────────────────────────────


@app.post("/scan/start", response_model=ScanStatusResponse)
async def start_scan(request: ScanStartRequest):
    """
    Start a new security scan.
    Creates a scan session and launches the scan asynchronously.
    """
    target_url = request.target_url.rstrip("/")

    # Validate URL
    if not target_url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL. Must start with http:// or https://",
        )

    # Create scan session in DB
    session = await create_scan_session(
        target_url=target_url,
        scan_type=request.scan_type,
        language=request.language,
    )

    # Launch scan in background
    asyncio.create_task(
        _safe_run_scan_pipeline(
            session.id, target_url, request.scan_type, request.language
        )
    )

    logger.info(f"Scan started: {session.id} for {target_url}")
    return ScanStatusResponse(
        id=session.id,
        target_url=target_url,
        status="pending",
        progress=0.0,
    )


@app.get("/scan/status/{session_id}", response_model=ScanStatusResponse)
async def get_scan_status(session_id: str):
    """Get the current status of a scan."""
    session = await get_scan_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Scan session not found")

    return ScanStatusResponse(
        id=session.id,
        target_url=session.target_url,
        status=session.status or "unknown",
        progress=(
            100.0
            if session.status == "completed"
            else 50.0 if session.status == "running" else 0.0
        ),
    )


@app.get("/scan/results/{session_id}", response_model=ScanResultResponse)
async def get_scan_results(session_id: str):
    """Get the complete results of a scan."""
    session = await get_scan_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Scan session not found")

    if session.status not in ("completed", "failed"):
        raise HTTPException(
            status_code=400,
            detail=f"Scan is still in progress. Status: {session.status}",
        )

    vulns = [
        VulnerabilityResponse(
            id=v.id,
            type=v.type,
            severity=v.severity,
            title=v.title,
            description=v.description,
            url=v.url,
            parameter=v.parameter,
            payload=v.payload,
            evidence=v.evidence,
            remediation=v.remediation,
            cvss_score=v.cvss_score,
        )
        for v in (session.vulnerabilities or [])
    ]

    return ScanResultResponse(
        id=session.id,
        target_url=session.target_url,
        status=session.status,
        scan_type=session.scan_type,
        security_score=session.security_score,
        risk_level=session.risk_level,
        ai_summary=session.ai_summary,
        vulnerabilities=vulns,
        created_at=session.created_at.isoformat() if session.created_at else "",
        language=session.language,
    )


@app.get("/history", response_model=List[HistoryItem])
async def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Get scan history."""
    sessions = await get_scan_history(limit=limit, offset=offset)

    return [
        HistoryItem(
            id=s.id,
            target_url=s.target_url,
            status=s.status,
            security_score=s.security_score,
            risk_level=s.risk_level,
            vulnerability_count=len(s.vulnerabilities or []),
            created_at=s.created_at.isoformat() if s.created_at else "",
        )
        for s in sessions
    ]


@app.delete("/scan/{session_id}")
async def delete_scan(session_id: str):
    """Delete a scan session and its data."""
    success = await delete_scan_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scan session not found")
    return {"status": "deleted", "id": session_id}


# ─── PDF Report Endpoint ───────────────────────────────────────────


@app.get("/report/pdf/{session_id}")
async def download_pdf_report(
    session_id: str, language: str = Query(default="en", regex="^(en|tr)$")
):
    """Download a PDF security report for a completed scan."""
    session = await get_scan_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Scan session not found")

    if session.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Cannot generate report for incomplete scan",
        )

    # Convert SQLAlchemy models to dicts
    vulnerabilities = [
        {
            "type": v.type,
            "severity": v.severity,
            "title": v.title,
            "description": v.description or "",
            "url": v.url or "",
            "parameter": v.parameter or "",
            "payload": v.payload or "",
            "evidence": v.evidence or "",
            "remediation": v.remediation or "",
            "cvss_score": v.cvss_score or 0,
        }
        for v in (session.vulnerabilities or [])
    ]

    session_data = {
        "target_url": session.target_url,
        "security_score": session.security_score or 0,
        "risk_level": session.risk_level or "info",
        "ai_summary": session.ai_summary or "",
        "remediation_steps": [],
    }

    try:
        pdf_bytes = generate_pdf(session_data, vulnerabilities, language=language)
        filename = f"webscanpro_report_{session.id[:8]}_{language}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes)),
            },
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {type(e).__name__}: {str(e)}",
        )


# ─── Scan Pipeline ─────────────────────────────────────────────────


async def _safe_run_scan_pipeline(
    session_id: str,
    target_url: str,
    scan_type: str,
    language: str,
) -> None:
    """
    Run the complete scan pipeline asynchronously.
    Includes passive scan, active scan, and AI analysis.
    Uses runtime settings from Flutter with .env fallbacks.
    """
    logger.info(f"Starting scan pipeline: {session_id}")

    # Resolve effective settings (runtime overrides with .env fallbacks)
    effective_timeout = _runtime_settings.get("scan_timeout", settings.scan_timeout)
    effective_retries = _runtime_settings.get("max_retries", settings.max_retries)
    effective_model = _runtime_settings.get("deepseek_model", settings.deepseek_model)
    effective_api_key = _runtime_settings.get(
        "deepseek_api_key", settings.deepseek_api_key
    )
    effective_waf = _runtime_settings.get("waf_evasion", True)
    effective_stealth = _runtime_settings.get("stealth_mode", True)

    # Log effective values (mask API key)
    logger.info(
        f"Scan started with: timeout={effective_timeout}, "
        f"retries={effective_retries}, model={effective_model}, "
        f"waf_evasion={effective_waf}, stealth={effective_stealth}"
    )

    try:
        # Update status to running
        await update_scan_status(session_id, status="running")

        all_vulnerabilities = []

        # Phase 1: Passive Scan (always runs)
        logger.info(f"[{session_id}] Running passive scan...")
        try:
            from scanners.passive_scanner import PassiveScanner

            passive = PassiveScanner(target_url, language=language)
            passive_results = await passive.run()
            for v in passive_results:
                vuln = await add_vulnerability(
                    session_id=session_id,
                    vuln_type=v["type"],
                    severity=v["severity"],
                    title=v["title"],
                    description=v.get("description", ""),
                    url=v.get("url", ""),
                    parameter=v.get("parameter"),
                    payload=v.get("payload"),
                    evidence=v.get("evidence", ""),
                    remediation=v.get("remediation", ""),
                    cvss_score=v.get("cvss_score"),
                )
                all_vulnerabilities.append(
                    {
                        "type": vuln.type,
                        "severity": vuln.severity,
                        "title": vuln.title,
                        "description": vuln.description or "",
                    }
                )
            logger.info(
                f"[{session_id}] Passive scan complete: {len(passive_results)} findings"
            )
        except Exception as e:
            logger.error(f"[{session_id}] Passive scan failed: {e}")

        # Phase 2: Active Scan (if full or active)
        if scan_type in ("full", "active"):
            logger.info(f"[{session_id}] Running active scan...")
            try:
                from scanners.active_scanner import ActiveScanner

                active = ActiveScanner(
                    target_url,
                    language=language,
                    timeout=effective_timeout,
                    max_retries=effective_retries,
                )
                active_results = await active.run()
                for v in active_results:
                    vuln = await add_vulnerability(
                        session_id=session_id,
                        vuln_type=v["type"],
                        severity=v["severity"],
                        title=v["title"],
                        description=v.get("description", ""),
                        url=v.get("url", ""),
                        parameter=v.get("parameter"),
                        payload=v.get("payload"),
                        evidence=v.get("evidence", ""),
                        remediation=v.get("remediation", ""),
                        cvss_score=v.get("cvss_score"),
                    )
                    all_vulnerabilities.append(
                        {
                            "type": vuln.type,
                            "severity": vuln.severity,
                            "title": vuln.title,
                            "description": vuln.description or "",
                        }
                    )
                logger.info(
                    f"[{session_id}] Active scan complete: {len(active_results)} findings"
                )
            except Exception as e:
                logger.error(f"[{session_id}] Active scan failed: {e}")

        # Phase 3: AI Analysis
        logger.info(f"[{session_id}] Running AI analysis...")
        try:
            ai_result = await deepseek_client.analyze_vulnerabilities(
                all_vulnerabilities,
                target_url,
                language=language,
            )
            security_score = ai_result.get("security_score")
            risk_level = ai_result.get("risk_level")
            ai_summary = ai_result.get("summary")

            await update_scan_status(
                session_id=session_id,
                status="completed",
                security_score=security_score,
                risk_level=risk_level,
                ai_summary=ai_summary,
                scan_metadata={"ai_analysis": ai_result},
            )
            logger.info(f"[{session_id}] AI analysis complete. Score: {security_score}")
        except Exception as e:
            logger.error(f"[{session_id}] AI analysis failed: {e}")
            # Complete scan even without AI
            await update_scan_status(
                session_id=session_id,
                status="completed",
                scan_metadata={"ai_error": str(e)},
            )

    except Exception as e:
        logger.error(
            f"[{session_id}] Scan pipeline failed: {type(e).__name__}: {e}",
            exc_info=True,
        )
        try:
            await update_scan_status(
                session_id,
                status="failed",
                error_message=str(e),
                scan_metadata={"error": str(e)},
            )
        except Exception as update_error:
            logger.error(
                f"[{session_id}] Failed to update scan status: {type(update_error).__name__}: {update_error}",
                exc_info=True,
            )


if __name__ == "__main__":
    import multiprocessing
    import uvicorn

    # Mandatory for Windows PyInstaller EXEs to prevent silent crashes
    multiprocessing.freeze_support()

    # Run directly with the app object, NO strings, NO reload
    uvicorn.run(app, host="127.0.0.1", port=8000)
