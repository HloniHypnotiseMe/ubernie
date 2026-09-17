#!/usr/bin/env python3
"""
Web Department — RemotePay Client

Pluggable 3-tier fallback:
  1. /api/v1/payment-links  (SimplyBlu + ledger)  ← primary, proper architecture
  2. /api/v1/payments       (PayFast legacy)       ← fallback
  3. mock                   (local dev only)       ← last resort

Set REMOTEPAY_MODE in .env to force a specific mode:
  auto  → try primary, fall back to secondary, then mock
  live  → only try primary (fail if unavailable)
  legacy→ only try secondary
  mock  → skip HTTP entirely (returns fake link)
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

log = logging.getLogger("web-department.remotepay")


class RemotePayError(RuntimeError):
    """Raised when RemotePay cannot service a request in the current mode."""


class RemotePayClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_version: str = "v1",
        mode: Optional[str] = None,
        timeout: float = 20.0,
    ):
        self.base_url = (base_url or os.getenv("REMOTEPAY_API_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.api_version = api_version
        self.mode = (mode or os.getenv("REMOTEPAY_MODE", "auto")).lower()
        self.timeout = timeout

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------
    def create_payment(
        self,
        *,
        amount_minor: int,
        description: str,
        merchant_id: str,
        brand_id: str = "ubernie",
        source_system: str = "c6_web_department",
        customer_reference: Optional[str] = None,
        return_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a payment via whichever RemotePay path is available.

        Returns a normalized dict:
          {
            "provider_path": "payment-links" | "payments" | "mock",
            "payment_id": str,
            "transaction_id": str,
            "payment_url": str,
            "status": str,
            "currency": "ZAR",
            "amount_minor": int,
            "raw": {...}   # provider response
          }
        """
        idem = idempotency_key or f"idem_{uuid.uuid4().hex}"

        attempts = []
        if self.mode in ("auto", "live"):
            attempts.append(("payment-links", self._via_payment_links))
        if self.mode in ("auto", "legacy"):
            attempts.append(("payments", self._via_legacy_payments))
        if self.mode in ("auto", "mock") or not attempts:
            attempts.append(("mock", self._via_mock))

        last_error: Optional[Exception] = None
        for name, fn in attempts:
            try:
                result = fn(
                    amount_minor=amount_minor,
                    description=description,
                    merchant_id=merchant_id,
                    brand_id=brand_id,
                    source_system=source_system,
                    customer_reference=customer_reference,
                    return_url=return_url,
                    cancel_url=cancel_url,
                    idempotency_key=idem,
                    metadata=metadata or {},
                )
                log.info("RemotePay payment created via %s", name)
                return result
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                log.warning("RemotePay path '%s' failed: %s", name, exc)

        raise RemotePayError(f"All RemotePay paths failed; last error: {last_error}")

    # ----------------------------------------------------------------
    # Path 1: /payment-links (SimplyBlu + ledger) — preferred
    # ----------------------------------------------------------------
    def _via_payment_links(
        self,
        *,
        amount_minor: int,
        description: str,
        merchant_id: str,
        brand_id: str,
        source_system: str,
        customer_reference: Optional[str],
        return_url: Optional[str],
        cancel_url: Optional[str],
        idempotency_key: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/{self.api_version}/payment-links"
        payload = {
            "merchant_id": merchant_id,
            "brand_id": brand_id,
            "source_system": source_system,
            "customer_reference": customer_reference,
            "description": description,
            "amount_minor": amount_minor,
            "currency": "ZAR",
            "return_url": return_url,
            "cancel_url": cancel_url,
            "idempotency_key": idempotency_key,
            "metadata": metadata,
        }
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()

        return {
            "provider_path": "payment-links",
            "payment_id": data["payment_id"],
            "transaction_id": data["transaction_id"],
            "payment_url": data["payment_url"],
            "status": data.get("status", "pending"),
            "currency": data.get("currency", "ZAR"),
            "amount_minor": data.get("amount_minor", amount_minor),
            "raw": data,
        }

    # ----------------------------------------------------------------
    # Path 2: /payments (PayFast legacy)
    # ----------------------------------------------------------------
    def _via_legacy_payments(
        self,
        *,
        amount_minor: int,
        description: str,
        merchant_id: str,
        brand_id: str,
        source_system: str,
        customer_reference: Optional[str],
        return_url: Optional[str],
        cancel_url: Optional[str],
        idempotency_key: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/{self.api_version}/payments"
        payload = {
            "amount": amount_minor,
            "currency": "ZAR",
            # legacy expects customer_id from its in-memory customers_db;
            # we pass our merchant_id and hope it's registered.
            "customer_id": customer_reference or merchant_id,
            "return_url": return_url or "https://example.com/return",
            "cancel_url": cancel_url or "https://example.com/cancel",
            "item_name": description[:100],
            "item_description": description,
        }
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()

        return {
            "provider_path": "payments",
            "payment_id": data.get("transaction_id", f"legacy_{uuid.uuid4().hex[:12]}"),
            "transaction_id": data.get("transaction_id", ""),
            "payment_url": data.get("checkout_url", ""),
            "status": data.get("status", "pending"),
            "currency": "ZAR",
            "amount_minor": amount_minor,
            "raw": data,
        }

    # ----------------------------------------------------------------
    # Path 3: mock (local dev only)
    # ----------------------------------------------------------------
    def _via_mock(
        self,
        *,
        amount_minor: int,
        description: str,
        merchant_id: str,
        brand_id: str,
        source_system: str,
        customer_reference: Optional[str],
        return_url: Optional[str],
        cancel_url: Optional[str],
        idempotency_key: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        payment_id = f"pay_mock_{uuid.uuid4().hex[:16]}"
        transaction_id = f"txn_mock_{uuid.uuid4().hex[:16]}"
        # Mock gateway lives in web-department, not RemotePay. Return a relative
        # path so the API layer can rewrite it with the correct base URL.
        mock_url = f"/mock-checkout/{payment_id}"

        log.warning(
            "MOCK PAYMENT created (no real money moved) — payment_id=%s amount_minor=%d",
            payment_id,
            amount_minor,
        )

        return {
            "provider_path": "mock",
            "payment_id": payment_id,
            "transaction_id": transaction_id,
            "payment_url": mock_url,
            "status": "mock_pending",
            "currency": "ZAR",
            "amount_minor": amount_minor,
            "raw": {
                "warning": "This is a mock payment. No real money moved.",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "merchant_id": merchant_id,
                "brand_id": brand_id,
                "source_system": source_system,
                "idempotency_key": idempotency_key,
                "metadata": metadata,
            },
        }
