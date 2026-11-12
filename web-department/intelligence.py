"""UBERNIE-owned business discovery intake and evidence ledger.

This module deliberately separates source approval, job queuing, candidate
intake, and human review. It does not fetch arbitrary URLs or auto-publish data.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.dependencies import require_role
from db.engine import SessionLocal
from db.models import (
    BusinessCandidate,
    BusinessCandidateEvidence,
    IntelligenceJob,
    IntelligenceSource,
)

router = APIRouter(prefix="/api/intelligence", tags=["business-intelligence"])
admin_user = require_role("admin", "superadmin")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _host(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Only credential-free HTTPS URLs are accepted")
    return parsed.hostname.lower().rstrip(".")


def _normalise(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()


def _dedupe_key(name: str, city: str | None, province: str | None, website: str | None) -> str:
    website_host = urlparse(website).hostname.lower() if website else ""
    identity = "|".join((_normalise(name), _normalise(city), _normalise(province), website_host))
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def create_source(db: Session, *, name: str, base_url: str, purpose: str,
                  terms_reviewed: bool, collection_permitted: bool,
                  robots_reviewed: bool, enabled: bool, requests_per_minute: int,
                  created_by: str) -> IntelligenceSource:
    host = _host(base_url)
    if not 1 <= requests_per_minute <= 30:
        raise ValueError("requests_per_minute must be between 1 and 30")
    if enabled and not (terms_reviewed and collection_permitted and robots_reviewed):
        raise ValueError("A source cannot be enabled until terms, permission and robots review are recorded")
    source = IntelligenceSource(
        id=str(uuid.uuid4()), name=name.strip(), base_url=f"https://{host}",
        purpose=purpose.strip(), terms_reviewed=terms_reviewed,
        collection_permitted=collection_permitted, robots_reviewed=robots_reviewed,
        enabled=enabled, requests_per_minute=requests_per_minute,
        created_by=created_by, created_at=_now(),
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def queue_job(db: Session, *, source_id: str, requested_url: str,
              created_by: str) -> IntelligenceJob:
    source = db.get(IntelligenceSource, source_id)
    if source is None or not source.enabled:
        raise ValueError("Source is missing or disabled")
    if _host(requested_url) != urlparse(source.base_url).hostname:
        raise ValueError("Requested URL must belong to the registered source host")
    job = IntelligenceJob(
        id=str(uuid.uuid4()), source_id=source.id, requested_url=requested_url,
        status="queued", attempts=0, created_by=created_by, created_at=_now(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def ingest_candidate(db: Session, *, source_id: str, source_url: str,
                     business_name: str, created_fields: dict[str, str | None]) -> tuple[BusinessCandidate, bool]:
    source = db.get(IntelligenceSource, source_id)
    if source is None or not source.enabled:
        raise ValueError("Source is missing or disabled")
    if _host(source_url) != urlparse(source.base_url).hostname:
        raise ValueError("Evidence URL must belong to the registered source host")

    name = business_name.strip()
    if not name:
        raise ValueError("business_name is required")
    key = _dedupe_key(name, created_fields.get("city"), created_fields.get("province"), created_fields.get("website"))
    existing = db.scalar(select(BusinessCandidate).where(BusinessCandidate.dedupe_key == key))
    if existing is not None:
        return existing, True

    allowed = {"category", "city", "province", "address", "phone", "email", "website"}
    fields = {k: (v.strip() if isinstance(v, str) else v) for k, v in created_fields.items() if k in allowed}
    candidate = BusinessCandidate(
        id=str(uuid.uuid4()), dedupe_key=key, business_name=name,
        source_url=source_url, source_id=source.id, evidence=[],
        status="pending_review", discovered_at=_now(),
        **fields,
    )
    db.add(candidate)
    db.flush()

    evidence_rows = []
    for field_name, value in {"business_name": name, **fields}.items():
        if value:
            evidence_rows.append(BusinessCandidateEvidence(
                id=str(uuid.uuid4()), candidate_id=candidate.id,
                field_name=field_name, observed_value=str(value),
                source_url=source_url, observed_at=_now(),
                evidence_kind="public_business_source",
            ))
    db.add_all(evidence_rows)
    candidate.evidence = [
        {"field": row.field_name, "value": row.observed_value,
         "source_url": row.source_url, "observed_at": row.observed_at.isoformat()}
        for row in evidence_rows
    ]
    db.commit()
    db.refresh(candidate)
    return candidate, False


class SourceRequest(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    base_url: HttpUrl
    purpose: str = Field(min_length=8, max_length=500)
    terms_reviewed: bool = False
    collection_permitted: bool = False
    robots_reviewed: bool = False
    enabled: bool = False
    requests_per_minute: int = Field(default=6, ge=1, le=30)


class JobRequest(BaseModel):
    source_id: str
    requested_url: HttpUrl


class CandidateRequest(BaseModel):
    source_id: str
    source_url: HttpUrl
    business_name: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    province: str | None = Field(default=None, max_length=120)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=255)
    website: HttpUrl | None = None


class ReviewRequest(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")


def _session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/sources", status_code=201)
def register_source(body: SourceRequest, user: dict = Depends(admin_user), db: Session = Depends(_session)):
    try:
        payload = body.model_dump()\n        payload["base_url"] = str(payload["base_url"])\n        source = create_source(db, **payload, created_by=user["user_id"])
    except (ValueError, IntegrityError) as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc))
    return {"id": source.id, "name": source.name, "base_url": source.base_url,
            "enabled": source.enabled, "requests_per_minute": source.requests_per_minute}


@router.post("/jobs", status_code=202)
def create_job(body: JobRequest, user: dict = Depends(admin_user), db: Session = Depends(_session)):
    try:
        job = queue_job(db, source_id=body.source_id, requested_url=str(body.requested_url),
                        created_by=user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"id": job.id, "status": job.status, "message": "Queued; no fetch has run yet."}


@router.post("/candidates", status_code=201)
def create_candidate(body: CandidateRequest, user: dict = Depends(admin_user), db: Session = Depends(_session)):
    payload = body.model_dump()
    source_id = payload.pop("source_id")
    source_url = str(payload.pop("source_url"))
    business_name = payload.pop("business_name")
    payload["website"] = str(payload["website"]) if payload.get("website") else None
    try:
        candidate, duplicate = ingest_candidate(
            db, source_id=source_id, source_url=source_url,
            business_name=business_name, created_fields=payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"id": candidate.id, "business_name": candidate.business_name,
            "status": candidate.status, "duplicate": duplicate,
            "evidence_count": len(candidate.evidence or []),
            "message": "Candidate remains private and pending review."}


@router.post("/candidates/{candidate_id}/review")
def review_candidate(candidate_id: str, body: ReviewRequest,
                     user: dict = Depends(admin_user), db: Session = Depends(_session)):
    candidate = db.get(BusinessCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status != "pending_review":
        raise HTTPException(status_code=409, detail="Candidate has already been reviewed")
    candidate.status = body.decision
    candidate.reviewed_by = user["user_id"]
    candidate.reviewed_at = _now()
    db.commit()
    return {"id": candidate.id, "status": candidate.status,
            "message": "Review recorded. This endpoint does not publish the candidate."}


@router.post("/jobs/{job_id}/run")
async def run_intelligence_job(job_id: str, user: dict = Depends(admin_user),
                               db: Session = Depends(_session)):
    from intelligence_worker import execute_job

    try:
        return await execute_job(db, job_id)
    except ValueError as exc:
        code = str(exc)
        status_code = 404 if code == "job_not_found" else 409
        raise HTTPException(status_code=status_code, detail=code)
