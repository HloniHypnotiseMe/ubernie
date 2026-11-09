import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integration.catalogue import CatalogueError, canonicalize_cart


def _publish_catalogue(root, shop_id, products):
    data = root / shop_id / "data"
    data.mkdir(parents=True)
    (data / "products.json").write_text(json.dumps(products), encoding="utf-8")


def test_checkout_uses_published_prices_and_names_not_client_values(tmp_path):
    _publish_catalogue(
        tmp_path,
        "shop_1",
        [{"id": "tea", "name": "House Tea", "price": 12.34}],
    )

    items, total_minor = canonicalize_cart(
        shop_id="shop_1",
        items=[{"id": "tea", "name": "Fake name", "price": 0.01, "qty": 2}],
        generated_sites_dir=tmp_path,
    )

    assert total_minor == 2468
    assert items == [{"id": "tea", "name": "House Tea", "price": 12.34, "qty": 2}]


def test_checkout_rejects_products_not_in_published_catalogue(tmp_path):
    _publish_catalogue(tmp_path, "shop_1", [{"id": "tea", "name": "House Tea", "price": 12.34}])

    with pytest.raises(CatalogueError, match="not in this shop"):
        canonicalize_cart(
            shop_id="shop_1",
            items=[{"id": "not-listed", "price": 0.01, "qty": 1}],
            generated_sites_dir=tmp_path,
        )


@pytest.mark.parametrize("shop_id", ["../outside", "..", "shop/other", ""])
def test_checkout_rejects_unsafe_shop_identifiers(tmp_path, shop_id):
    with pytest.raises(CatalogueError, match="Invalid shop identifier"):
        canonicalize_cart(
            shop_id=shop_id,
            items=[{"id": "tea", "qty": 1}],
            generated_sites_dir=tmp_path,
        )


@pytest.mark.parametrize("quantity", [0, -1, 1001, True, "2"])
def test_checkout_rejects_invalid_quantities(tmp_path, quantity):
    _publish_catalogue(tmp_path, "shop_1", [{"id": "tea", "name": "House Tea", "price": 12.34}])

    with pytest.raises(CatalogueError, match="quantity"):
        canonicalize_cart(
            shop_id="shop_1",
            items=[{"id": "tea", "qty": quantity}],
            generated_sites_dir=tmp_path,
        )


@pytest.mark.parametrize("price", [-1, "NaN", "Infinity", "not-a-price", None])
def test_checkout_rejects_invalid_published_prices(tmp_path, price):
    _publish_catalogue(tmp_path, "shop_1", [{"id": "tea", "name": "House Tea", "price": price}])

    with pytest.raises(CatalogueError, match="price is invalid"):
        canonicalize_cart(
            shop_id="shop_1",
            items=[{"id": "tea", "qty": 1}],
            generated_sites_dir=tmp_path,
        )


def test_checkout_rejects_prices_outside_database_integer_range(tmp_path):
    _publish_catalogue(
        tmp_path,
        "shop_1",
        [{"id": "expensive", "name": "Expensive Item", "price": 21474836.48}],
    )

    with pytest.raises(CatalogueError, match="price is invalid"):
        canonicalize_cart(
            shop_id="shop_1",
            items=[{"id": "expensive", "qty": 1}],
            generated_sites_dir=tmp_path,
        )


def test_checkout_rejects_total_outside_database_integer_range(tmp_path):
    _publish_catalogue(
        tmp_path,
        "shop_1",
        [{"id": "expensive", "name": "Expensive Item", "price": 10000000}],
    )

    with pytest.raises(CatalogueError, match="Cart total exceeds"):
        canonicalize_cart(
            shop_id="shop_1",
            items=[{"id": "expensive", "qty": 300}],
            generated_sites_dir=tmp_path,
        )
