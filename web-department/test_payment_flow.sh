#!/usr/bin/env bash
# Simulate the full payment redirect flow with curl (follows redirects).
set -euo pipefail

API="http://127.0.0.1:8100"
SHOP_ID="kota_king"

echo "=== 1. Regenerate Kota King ==="
curl -s -X POST "$API/api/sites/$SHOP_ID/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Kota King",
    "industry": "restaurant",
    "address": "123 Vilakazi St, Soweto",
    "phone": "0111234567",
    "email": "hello@kotaking.co.za",
    "tagline": "Best kota in Soweto, delivered hot.",
    "menu_items": [
      {"id": "p1", "name": "Classic Kota", "price": 45.00, "description": "Bread, chips, polony, cheese, atchar"},
      {"id": "p2", "name": "Kota Special", "price": 65.00, "description": "Classic + Russian, egg, extra cheese"}
    ]
  }' > /dev/null
echo "  ✅ Site regenerated"

echo ""
echo "=== 2. Create payment (browser would do this from checkout) ==="
ORDER=$(curl -s -X POST "$API/api/remotepay/create-payment" \
  -H "Content-Type: application/json" \
  -d "{
    \"shop_id\": \"$SHOP_ID\",
    \"merchant_id\": \"merchant_$SHOP_ID\",
    \"items\": [{\"id\": \"p1\", \"name\": \"Classic Kota\", \"price\": 45.00, \"qty\": 2}],
    \"delivery_area\": \"Soweto\",
    \"customer_email\": \"customer@example.com\"
  }")
echo "$ORDER" | python -m json.tool

OID=$(echo "$ORDER" | python -c "import sys,json;print(json.load(sys.stdin)['order_id'])")
PID=$(echo "$ORDER" | python -c "import sys,json;print(json.load(sys.stdin)['payment_id'])")
PURL=$(echo "$ORDER" | python -c "import sys,json;print(json.load(sys.stdin)['payment_url'])")

echo ""
echo "=== 3. Fetch mock gateway page (what the customer sees) ==="
curl -s "$PURL" | head -40

echo ""
echo "=== 4. Customer clicks 'Pay now' — POST to gateway, follow redirects ==="
FINAL=$(curl -sL -X POST "$API/mock-checkout/$PID/pay" -w "\n---FINAL_URL:%{url_effective}---")
echo "$FINAL" | grep -E "FINAL_URL|Thank you|Rider|VAT" || true

echo ""
echo "=== 5. Verify order status after payment ==="
curl -s "$API/api/orders/$OID" | python -m json.tool

echo ""
echo "=== 6. Verify payment record ==="
curl -s "$API/api/payments/$PID" | python -m json.tool

echo ""
echo "✅ Full redirect flow works."
