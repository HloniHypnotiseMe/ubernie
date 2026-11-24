"""Deterministic business extraction using the BSD-3-Clause Scrapling parser."""
from __future__ import annotations

import json
from urllib.parse import urljoin, urlparse

from scrapling import Selector


BUSINESS_TYPES = {
    "LocalBusiness", "Organization", "Corporation", "Store",
    "ProfessionalService", "HomeAndConstructionBusiness",
    "AutomotiveBusiness", "FoodEstablishment", "MedicalBusiness",
}


def _walk_jsonld(value):
    if isinstance(value, list):
        for item in value:
            yield from _walk_jsonld(item)
    elif isinstance(value, dict):
        yield value
        for child in value.values():
            if isinstance(child, (dict, list)):
                yield from _walk_jsonld(child)


def _text(value):
    if isinstance(value, str):
        return value.strip() or None
    return None


def extract_business_entities(html: bytes, page_url: str) -> list[dict[str, str | None]]:
    """Extract only explicit Schema.org business entities; do not infer identity."""
    page = Selector(content=html, url=page_url)
    found: dict[str, dict[str, str | None]] = {}

    for raw in page.css('script[type="application/ld+json"]::text').getall():
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError):
            continue

        for node in _walk_jsonld(payload):
            raw_types = node.get("@type", [])
            types = {raw_types} if isinstance(raw_types, str) else set(raw_types or [])
            if not (types & BUSINESS_TYPES):
                continue

            name = _text(node.get("name"))
            if not name:
                continue

            address = node.get("address") or {}
            if isinstance(address, str):
                address = {"streetAddress": address}
            if not isinstance(address, dict):
                address = {}

            website = _text(node.get("url"))
            if website:
                website = urljoin(page_url, website)
                if urlparse(website).scheme != "https":
                    website = None

            record = {
                "business_name": name[:255],
                "category": next(iter(sorted(types & BUSINESS_TYPES)), None),
                "address": _text(address.get("streetAddress")),
                "city": _text(address.get("addressLocality")),
                "province": _text(address.get("addressRegion")),
                "phone": _text(node.get("telephone")),
                "email": _text(node.get("email")),
                "website": website,
            }
            key = "|".join((name.casefold(), (record["city"] or "").casefold(), (record["website"] or "").casefold()))
            found.setdefault(key, record)

    return list(found.values())
