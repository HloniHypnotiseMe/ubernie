import ast
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_dependencies_cover_imports():
    req = (ROOT / "requirements.txt").read_text()
    for package in ("bcrypt", "python-jose", "psycopg", "pytest"):
        assert package in req


def test_production_contract_disables_mock_fallback():
    api = (ROOT / "api.py").read_text()
    env = (ROOT / ".env.example").read_text()
    assert "REMOTEPAY_MODE" in api
    assert "REMOTEPAY_WEBHOOK_SECRET" in api
    assert "REMOTEPAY_MODE: live" in (ROOT / "docker-compose.production.yml").read_text()
    assert "Payment is not verified as paid" in api


def test_internal_apps_do_not_hardcode_localhost_api():
    for name in ("dashboard/index.html", "rider/index.html", "signup/index.html", "track/index.html"):
        text = (ROOT / "static" / name).read_text()
        assert "127.0.0.1:8100" not in text
        assert "window.UBERNIE_WEB_DEPARTMENT_API" in text


def test_production_container_contract_exists():
    assert (ROOT / "Dockerfile").exists()
    assert (ROOT / "docker-compose.production.yml").exists()
    assert (ROOT / "PRODUCTION.md").exists()


def test_mock_checkout_routes_are_blocked_in_production():
    source = (ROOT / "api.py").read_text()
    tree = ast.parse(source)
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    guard = functions["_block_mock_checkout_in_production"]
    checks_production = any(
        isinstance(node, ast.Compare)
        and any(isinstance(child, ast.Constant) and child.value == "production" for child in ast.walk(node))
        for node in ast.walk(guard)
    )
    returns_not_found = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "HTTPException"
        and any(
            keyword.arg == "status_code"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == 404
            for keyword in node.keywords
        )
        for node in ast.walk(guard)
    )
    assert checks_production
    assert returns_not_found

    for route_name in (
        "mock_checkout_page",
        "mock_checkout_pay",
        "mock_checkout_cancel",
        "mock_return",
    ):
        route = functions[route_name]
        calls_guard = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_block_mock_checkout_in_production"
            for node in ast.walk(route)
        )
        assert calls_guard, f"{route_name} must block mock checkout in production"


def test_mock_checkout_handlers_return_404_in_production():
    script = """
import asyncio
import api
from fastapi import HTTPException

api.ENVIRONMENT = "production"

async def main():
    calls = [
        api.mock_checkout_page("payment-test", None),
        api.mock_checkout_pay("payment-test", None),
        api.mock_checkout_cancel("payment-test", None),
        api.mock_return("payment-test"),
    ]
    for call in calls:
        try:
            await call
        except HTTPException as exc:
            assert exc.status_code == 404, exc.status_code
        else:
            raise AssertionError("A mock checkout route was reachable in production mode")

asyncio.run(main())
"""
    env = os.environ.copy()
    env["ENVIRONMENT"] = "development"
    env["DATABASE_URL"] = "sqlite:///:memory:"
    env["REMOTEPAY_MODE"] = "mock"
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_checkout_endpoint_uses_server_catalogue_and_server_merchant_identity():
    source = (ROOT / "api.py").read_text()
    start = source.index("async def create_payment(")
    end = source.index("\n\n@app.post(\"/api/orders/confirm\")", start)
    handler = source[start:end]
    assert "canonicalize_cart(" in handler
    assert "merchant_id = f\"merchant_{req.shop_id}\"" in handler
    assert "sum(i.price * i.qty for i in req.items)" not in handler
    assert "items=canonical_items" in handler


def test_webhook_uses_currency_check_and_monotonic_state_transitions():
    source = (ROOT / "api.py").read_text()
    start = source.index("async def remotepay_webhook(")
    end = source.index("\n\n@app.get(\"/api/payments/{payment_id}\")", start)
    handler = source[start:end]
    assert 'req.currency.upper() != payment["currency"].upper()' in handler
    assert "repo.mark_payment_paid(req.payment_id)" in handler
    assert "repo.mark_order_paid(payment[\"order_id\"], req.payment_id)" in handler
    assert "repo.mark_payment_cancelled(req.payment_id, status=target_status)" in handler
    assert 'repo.update_order_status(payment["order_id"], status="paid"' not in handler


def test_checkout_persists_remote_pay_transaction_identity():
    source = (ROOT / "api.py").read_text()
    start = source.index("async def create_payment(")
    end = source.index("\n\n@app.post(\"/api/orders/confirm\")", start)
    handler = source[start:end]
    assert 'transaction_id = payment.get("transaction_id")' in handler
    assert "provider_reference=transaction_id" in handler

    webhook_start = source.index("async def remotepay_webhook(")
    webhook_end = source.index("\n\n@app.get(\"/api/payments/{payment_id}\")", webhook_start)
    webhook = source[webhook_start:webhook_end]
    assert 'req.transaction_id != payment["provider_reference"]' in webhook
    assert 'req.merchant_id != order["merchant_id"]' in webhook
    assert 'req.brand_id != "ubernie"' in webhook
    assert 'req.source_system != "c6_web_department"' in webhook
