#!/usr/bin/env bash
# End-to-end test: generate a shop site, verify it's served, verify its
# JS calls the API correctly (via curl to the same endpoints).
set -euo pipefail

API="http://127.0.0.1:8100"
SHOP_ID="test_shop_$(date +%s)"

echo "=== 1. Generate a site for $SHOP_ID ==="
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
      {"id": "p1", "name": "Classic Kota", "price": 45.00},
      {"id": "p2", "name": "Kota Special", "price": 65.00}
    ]
  }' | python -m json.tool

echo ""
echo "=== 2. Fetch generated homepage ==="
curl -s "$API/sites/$SHOP_ID/index.html" | head -20

echo ""
echo "=== 3. Fetch generated config (should point at API) ==="
curl -s "$API/sites/$SHOP_ID/assets/c6-config.js"

echo ""
echo "=== 4. Simulate checkout: create payment ==="
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

echo ""
echo "=== 5. Confirm order (fires dispatch) ==="
curl -s -X POST "$API/api/orders/confirm" \
  -H "Content-Type: application/json" \
  -d "{\"order_id\": \"$OID\", \"payment_id\": \"$PID\"}" | python -m json.tool

echo ""
echo "✅ Generated site test complete."
echo ""
echo "Open in browser:"
echo "  $API/sites/$SHOP_ID/index.html"
echo "  $API/sites/$SHOP_ID/checkout.html"
