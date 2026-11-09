import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_payment_state_transitions_are_monotonic_and_idempotent(tmp_path):
    script = """
from db.engine import init_db
from db import repositories as repo
from db.repositories import PaymentStateConflict, OrderStateConflict

init_db()

def create(order_id, payment_id):
    repo.create_order(
        order_id=order_id,
        shop_id="shop_1",
        merchant_id="merchant_shop_1",
        items=[],
        total_minor=1000,
    )
    repo.create_payment_record(
        payment_id=payment_id,
        order_id=order_id,
        amount_minor=1000,
        provider="remotepay",
    )

create("order-paid", "payment-paid")
paid = repo.mark_payment_paid("payment-paid")
assert paid["status"] == "paid"
assert repo.mark_payment_paid("payment-paid")["status"] == "paid"
try:
    repo.mark_payment_cancelled("payment-paid")
except PaymentStateConflict:
    pass
else:
    raise AssertionError("paid payment regressed to cancelled")

order = repo.mark_order_paid("order-paid", "payment-paid")
assert order["status"] == "paid"
repo.update_order_status("order-paid", status="confirmed", payment_id="payment-paid", mark_confirmed=True)
assert repo.mark_order_paid("order-paid", "payment-paid")["status"] == "confirmed"
try:
    repo.mark_order_paid("order-paid", "different-payment")
except OrderStateConflict:
    pass
else:
    raise AssertionError("order accepted a different payment")

create("order-failed", "payment-failed")
failed = repo.mark_payment_cancelled("payment-failed", status="failed")
assert failed["status"] == "failed"
assert repo.mark_payment_cancelled("payment-failed", status="failed")["status"] == "failed"
try:
    repo.mark_payment_paid("payment-failed")
except PaymentStateConflict:
    pass
else:
    raise AssertionError("failed payment regressed to paid")

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

create("order-race", "payment-race")
barrier = Barrier(2)

def race_paid():
    barrier.wait()
    try:
        return repo.mark_payment_paid("payment-race")["status"]
    except PaymentStateConflict:
        return "conflict"

def race_cancelled():
    barrier.wait()
    try:
        return repo.mark_payment_cancelled("payment-race")["status"]
    except PaymentStateConflict:
        return "conflict"

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(lambda fn: fn(), [race_paid, race_cancelled]))
assert results.count("conflict") == 1, results
assert repo.get_payment("payment-race")["status"] in {"paid", "cancelled"}
"""
    env = os.environ.copy()
    env["ENVIRONMENT"] = "development"
    env["DATABASE_URL"] = f"sqlite:///{tmp_path / 'payment-state.db'}"
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_webhook_rejects_currency_mismatch_before_state_mutation(tmp_path):
    script = """
import asyncio
import api
from api import RemotePayWebhookRequest
from fastapi import HTTPException

api.ENVIRONMENT = "development"
api.repo.get_payment = lambda payment_id: {
    "payment_id": payment_id,
    "order_id": "order-1",
    "amount_minor": 1000,
    "currency": "ZAR",
    "status": "pending",
}
api.repo.mark_payment_paid = lambda payment_id: (_ for _ in ()).throw(
    AssertionError("payment state mutated despite currency mismatch")
)

class FakeRequest:
    headers = {}
    async def body(self):
        return b"{}"

try:
    asyncio.run(api.remotepay_webhook(
        RemotePayWebhookRequest(payment_id="payment-1", status="paid", currency="USD"),
        FakeRequest(),
    ))
except HTTPException as exc:
    assert exc.status_code == 409
else:
    raise AssertionError("currency mismatch was accepted")
"""
    env = os.environ.copy()
    env["ENVIRONMENT"] = "development"
    env["DATABASE_URL"] = f"sqlite:///{tmp_path / 'webhook-currency.db'}"
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
