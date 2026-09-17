#!/usr/bin/env python3
"""
Web Department — Tax AI Hook

Every confirmed order is logged for VAT.
Real Tax AI integration comes later; for now this appends to a local ledger file.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

log = logging.getLogger("web-department.taxai")

_LEDGER_PATH = Path(os.getenv("TAXAI_LOCAL_LEDGER", "data/tax_ledger.jsonl"))
_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)


def record_transaction(
    *,
    order_id: str,
    payment_id: str,
    merchant_id: str,
    amount_minor: int,
    vat_minor: int,
    description: str,
    customer_reference: str | None = None,
) -> Dict[str, Any]:
    """Append one immutable tax record."""
    entry = {
        "order_id": order_id,
        "payment_id": payment_id,
        "merchant_id": merchant_id,
        "amount_minor": amount_minor,
        "vat_minor": vat_minor,
        "vat_rate": 0.15,
        "currency": "ZAR",
        "description": description,
        "customer_reference": customer_reference,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "source_system": "c6_web_department",
    }

    with _LEDGER_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")

    log.info("Tax record appended: order=%s vat_minor=%d", order_id, vat_minor)
    return entry


def calculate_vat(amount_minor_inclusive: int, vat_rate: float = 0.15) -> int:
    """Compute the VAT portion of a VAT-inclusive amount (ZAR)."""
    return round(amount_minor_inclusive * vat_rate / (1 + vat_rate))
