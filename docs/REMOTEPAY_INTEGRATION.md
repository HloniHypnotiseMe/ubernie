# Ubernie → RemotePay Integration

Ubernie now has a dedicated RemotePay client boundary. Ubernie business/application code does not call SimplyBLU, PayFast, or another processor directly.

## Configuration

Set these environment variables in the Ubernie runtime:

- `REMOTEPAY_API_BASE_URL`
- `REMOTEPAY_API_TIMEOUT` (optional; default 15 seconds)
- `REMOTEPAY_MERCHANT_ID`
- `REMOTEPAY_BRAND_ID`

Do not commit credentials or live URLs containing secrets.

## Flow

`Ubernie Business → RemotePayActivationAgent → RemotePayClient → RemotePay /api/v1/payment-links`

The request includes the Ubernie source system, merchant/brand identity, business reference, amount in ZAR minor units, and an idempotency key.

## Current boundary

This integration creates a RemotePay payment-link request. It does not yet execute a live payment, process provider callbacks inside Ubernie, or settle funds. Those remain RemotePay responsibilities.

The payment-link amount must be supplied by the calling commercial flow; this integration intentionally does not invent product prices.
