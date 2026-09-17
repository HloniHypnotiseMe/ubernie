#!/usr/bin/env bash
# Simulate a zone going from empty → active via the two-sided waitlist.
set -euo pipefail

API="http://127.0.0.1:8100"

echo "=== 1. Zone status before any signups ==="
curl -s "$API/api/waitlist/zone/Soweto" | python -m json.tool

echo ""
echo "=== 2. Register 15 shops in Soweto ==="
for i in $(seq 1 15); do
  curl -s -X POST "$API/api/waitlist/shop" \
    -H "Content-Type: application/json" \
    -d "{
      \"business_name\": \"Shop $i\",
      \"area\": \"Soweto\",
      \"industry\": \"retail\",
      \"email\": \"shop$i@example.com\",
      \"phone\": \"01100000$i\"
    }" > /dev/null
  echo "  Shop $i registered"
done

echo ""
echo "=== 3. Zone status after 15 shops, 0 riders ==="
curl -s "$API/api/waitlist/zone/Soweto" | python -m json.tool

echo ""
echo "=== 4. Register 3 riders in Soweto ==="
for i in $(seq 1 3); do
  curl -s -X POST "$API/api/waitlist/rider" \
    -H "Content-Type: application/json" \
    -d "{
      \"full_name\": \"Rider $i\",
      \"area\": \"Soweto\",
      \"vehicle\": \"Zeebee Greenscooter\",
      \"phone\": \"07200000$i\",
      \"email\": \"rider$i@example.com\",
      \"licence_number\": \"DL-000$i\"
    }" > /dev/null
  echo "  Rider $i registered"
done

echo ""
echo "=== 5. Zone status after 15 shops + 3 riders — should be ACTIVE ==="
curl -s "$API/api/waitlist/zone/Soweto" | python -m json.tool

echo ""
echo "=== 6. Delivery check — should now be available ==="
curl -s "$API/api/delivery/check?area=Soweto" | python -m json.tool

echo ""
echo "=== 7. Delivery check for inactive area (Sandton) — should be NOT available ==="
curl -s "$API/api/delivery/check?area=Sandton" | python -m json.tool

echo ""
echo "=== 8. All zones summary ==="
curl -s "$API/api/waitlist/zones" | python -m json.tool

echo ""
echo "✅ Test complete."
