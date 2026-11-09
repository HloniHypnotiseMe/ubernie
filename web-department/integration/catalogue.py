"""Server-authoritative catalogue lookup and checkout price calculation."""
from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


class CatalogueError(ValueError):
    """Raised when a checkout cannot be priced from a published catalogue."""


_SHOP_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_MAX_QUANTITY = 1000
_MAX_TOTAL_MINOR = 2_147_483_647


def canonicalize_cart(
    *,
    shop_id: str,
    items: list[dict[str, Any]],
    generated_sites_dir: str | Path,
) -> tuple[list[dict[str, Any]], int]:
    """Replace all client-supplied names/prices with the published shop catalogue."""
    if not isinstance(shop_id, str) or not _SHOP_ID.fullmatch(shop_id):
        raise CatalogueError("Invalid shop identifier")

    root = Path(generated_sites_dir).resolve()
    catalogue_path = (root / shop_id / "data" / "products.json").resolve()
    if root not in catalogue_path.parents:
        raise CatalogueError("Invalid shop catalogue path")
    if not catalogue_path.is_file():
        raise CatalogueError("Shop catalogue is not published")

    try:
        catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogueError("Published shop catalogue is unavailable or invalid") from exc

    if not isinstance(catalogue, list):
        raise CatalogueError("Published shop catalogue has an invalid format")

    products: dict[str, tuple[str, int]] = {}
    for product in catalogue:
        if not isinstance(product, dict):
            raise CatalogueError("Published shop catalogue contains an invalid product")
        product_id = str(product.get("id", "")).strip()
        name = str(product.get("name", "")).strip()
        if not product_id or not name or product_id in products:
            raise CatalogueError("Published shop catalogue contains missing or duplicate product identity")
        try:
            price = Decimal(str(product.get("price")))
            if not price.is_finite() or price < 0:
                raise InvalidOperation
            price_minor = int((price * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            if price_minor > _MAX_TOTAL_MINOR:
                raise InvalidOperation
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise CatalogueError(f"Published price is invalid for product {product_id}") from exc
        products[product_id] = (name, price_minor)

    if not items:
        raise CatalogueError("Cart is empty")

    canonical_items: list[dict[str, Any]] = []
    total_minor = 0
    for item in items:
        product_id = str(item.get("id", "")).strip()
        if product_id not in products:
            raise CatalogueError(f"Product {product_id or '(missing)'} is not in this shop's published catalogue")
        quantity = item.get("qty")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= _MAX_QUANTITY:
            raise CatalogueError("Product quantity is outside the allowed range")

        name, price_minor = products[product_id]
        total_minor += price_minor * quantity
        if total_minor > _MAX_TOTAL_MINOR:
            raise CatalogueError("Cart total exceeds the supported payment amount")
        canonical_items.append({
            "id": product_id,
            "name": name,
            "price": price_minor / 100,
            "qty": quantity,
        })

    return canonical_items, total_minor
