#!/usr/bin/env bash
# End-to-end test: generate a full storefront, verify all pages + data,
# verify products.json is written, verify static serving works.
set -euo pipefail

API="http://127.0.0.1:8100"
SHOP_ID="kota_king"

echo "=== 1. Generate a full storefront for $SHOP_ID ==="
curl -s -X POST "$API/api/sites/$SHOP_ID/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Kota King",
    "industry": "restaurant",
    "address": "123 Vilakazi St, Soweto",
    "phone": "0111234567",
    "email": "hello@kotaking.co.za",
    "tagline": "Best kota in Soweto, delivered hot.",
    "story": "Kota King has been serving Soweto since 2015. From classic kotas to our famous specials, we bring the taste of the township straight to your door.",
    "menu_items": [
      {"id": "p1", "name": "Classic Kota", "description": "Bread, chips, polony, cheese, atchar", "price": 45.00, "category": "Kota"},
      {"id": "p2", "name": "Kota Special", "description": "Classic + Russian, egg, extra cheese", "price": 65.00, "category": "Kota"},
      {"id": "p3", "name": "Kota Full House", "description": "Everything in the kitchen on a quarter loaf", "price": 85.00, "category": "Kota"},
      {"id": "p4", "name": "Russian & Chips", "description": "Grilled Russian, slap chips, atchar", "price": 40.00, "category": "Combos"},
      {"id": "p5", "name": "Coke 500ml", "description": "Ice cold", "price": 15.00, "category": "Drinks"},
      {"id": "p6", "name": "Water 500ml", "description": "Still water", "price": 10.00, "category": "Drinks"}
    ]
  }' | python -m json.tool

echo ""
echo "=== 2. Verify generated files ==="
SITE_DIR="generated-sites/$SHOP_ID"
for f in index.html menu.html about.html contact.html checkout.html thank-you.html \
         assets/c6-config.js assets/c6-api.js assets/products.js assets/cart.js \
         data/products.json data/shop.json; do
  if [ -f "$SITE_DIR/$f" ]; then
    size=$(wc -c < "$SITE_DIR/$f")
    echo "  ✅ $f ($size bytes)"
  else
    echo "  ❌ MISSING: $f"
  fi
done

echo ""
echo "=== 3. products.json contents ==="
cat "$SITE_DIR/data/products.json"

echo ""
echo "=== 4. shop.json contents ==="
cat "$SITE_DIR/data/shop.json"

echo ""
echo "=== 5. Homepage HTTP check ==="
curl -s -o /dev/null -w "  index.html: HTTP %{http_code}, %{size_download} bytes\n" "$API/sites/$SHOP_ID/index.html"
curl -s -o /dev/null -w "  menu.html:  HTTP %{http_code}, %{size_download} bytes\n" "$API/sites/$SHOP_ID/menu.html"
curl -s -o /dev/null -w "  c6-api.js:  HTTP %{http_code}, %{size_download} bytes\n" "$API/sites/$SHOP_ID/assets/c6-api.js"
curl -s -o /dev/null -w "  products.json: HTTP %{http_code}, %{size_download} bytes\n" "$API/sites/$SHOP_ID/data/products.json"

echo ""
echo "=== 6. Simulate checkout against the API (same as the browser would) ==="
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

curl -s -X POST "$API/api/orders/confirm" \
  -H "Content-Type: application/json" \
  -d "{\"order_id\": \"$OID\", \"payment_id\": \"$PID\"}" | python -m json.tool

echo ""
echo "✅ Test complete."
echo ""
echo "Open in browser:"
echo "  $API/sites/$SHOP_ID/index.html"
echo "  $API/sites/$SHOP_ID/menu.html"
echo "  $API/sites/$SHOP_ID/checkout.html"
