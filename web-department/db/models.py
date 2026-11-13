#!/usr/bin/env python3
"""Web Department — ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    role: Mapped[str] = mapped_column(String(16), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    area: Mapped[str | None] = mapped_column(String(128), index=True)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shop_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    vehicle: Mapped[str | None] = mapped_column(String(64), nullable=True)
    licence_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    record_type: Mapped[str] = mapped_column(String(16), index=True)
    area: Mapped[str] = mapped_column(String(128), index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(32))
    industry: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vehicle: Mapped[str | None] = mapped_column(String(64), nullable=True)
    licence_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    estimated_daily_orders: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="WAITING")
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    __table_args__ = (
        Index("ix_waitlist_area_type_status", "area", "record_type", "status"),
    )


class Zone(Base):
    __tablename__ = "zones"

    area: Mapped[str] = mapped_column(String(128), primary_key=True)
    shop_count: Mapped[int] = mapped_column(Integer, default=0)
    rider_count: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    shop_id: Mapped[str] = mapped_column(String(128), index=True)
    merchant_id: Mapped[str] = mapped_column(String(128))
    items: Mapped[list] = mapped_column(JSON)
    total_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="ZAR")
    delivery: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="awaiting_payment", index=True)
    payment_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    rider_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    vat_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(64), ForeignKey("orders.id"), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="ZAR")
    provider: Mapped[str] = mapped_column(String(32))
    provider_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    payment_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class RiderEvent(Base):
    __tablename__ = "rider_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rider_id: Mapped[str] = mapped_column(String(36), index=True)
    order_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)


class TaxRecord(Base):
    __tablename__ = "tax_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(64), index=True)
    payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    merchant_id: Mapped[str] = mapped_column(String(128), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    vat_minor: Mapped[int] = mapped_column(Integer)
    vat_rate: Mapped[float] = mapped_column(Float, default=0.15)
    currency: Mapped[str] = mapped_column(String(3), default="ZAR")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_system: Mapped[str] = mapped_column(String(64), default="c6_web_department")
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)


class IntelligenceSource(Base):
    """Approved public-information source registry; collection is disabled by default."""
    __tablename__ = "intelligence_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(180))
    base_url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    purpose: Mapped[str] = mapped_column(String(500))
    terms_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    collection_permitted: Mapped[bool] = mapped_column(Boolean, default=False)
    robots_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    requests_per_minute: Mapped[int] = mapped_column(Integer, default=6)
    created_by: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class IntelligenceJob(Base):
    """Durable crawl/intake job record. Queue execution is a separate worker concern."""
    __tablename__ = "intelligence_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("intelligence_sources.id"), index=True)
    requested_url: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(24), default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class BusinessCandidate(Base):
    """Discovered business record. Never public until separately reviewed and approved."""
    __tablename__ = "business_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dedupe_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    business_name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    province: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_url: Mapped[str] = mapped_column(String(2000))
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("intelligence_sources.id"), index=True)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(24), default="pending_review", index=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class BusinessCandidateEvidence(Base):
    """Append-only provenance for an observed business field."""
    __tablename__ = "business_candidate_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("business_candidates.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(80))
    observed_value: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(String(2000))
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)
    evidence_kind: Mapped[str] = mapped_column(String(40), default="public_web_claim")
