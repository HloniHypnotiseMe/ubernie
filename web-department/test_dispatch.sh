#!/usr/bin/env bash
# Full dispatch test:
#   1. Verify 3 riders exist in Soweto (from previous test)
#   2. Place order → confirm → verify rider assigned
#   3. Place 2nd order → verify a DIFFERENT rider is assigned (load balancing)
#   4. Complete first order → verify that rider returns to AVAILABLE
set -euo pipefail

API="http://127.0.0.1:8100"

echo "=== 1. Riders currently in Soweto ==="
curl -s "$API/api/riders/zone/Soweto" | python -m json.tool

echo ""
echo "=== 2. Create + confirm ORDER 1 ==="
ORDER1=$(curl -s -X POST "$API/api/remotepay/create-payment" \
  -H "Content-Type: application/json" \
  -d '{
    "shop_id": "shop_test_1",
    "merchant_id": "merchant_test_1",
    "items": [{"id": "p1", "name": "Kota", "price": 45.00, "qty": 1}],
    "delivery_area": "Soweto",
    "customer_email": "customer1@example.com"
  }')
echo "$ORDER1" | python -m json.tool
OID1=$(echo "$ORDER1" | python -c "import sys, json; print(json.load(sys.stdin)['order_id'])")
PID1=$(echo "$ORDER1" | python -c "import sys, json; print(json.load(sys.stdin)['payment_id'])")

CONFIRM1=$(curl -s -X POST "$API/api/orders/confirm" \
  -H "Content-Type: application/json" \
  -d "{\"order_id\": \"$OID1\", \"payment_id\": \"$PID1\"}")
echo "$CONFIRM1" | python -m json.tool

RIDER1_ID=$(echo "$CONFIRM1" | python -c "import sys, json; d=json.load(sys.stdin); print(d.get('dispatch',{}).get('rider',{}).get('id',''))")
echo "  → Assigned rider: $RIDER1_ID"

echo ""
echo "=== 3. Riders after ORDER 1 assignment (one should be ON_DELIVERY) ==="
curl -s "$API/api/riders/zone/Soweto" | python -m json.tool

echo ""
echo "=== 4. Create + confirm ORDER 2 (should get a different rider) ==="
ORDER2=$(curl -s -X POST "$API/api/remotepay/create-payment" \
  -H "Content-Type: application/json" \
  -d '{
    "shop_id": "shop_test_2",
    "merchant_id": "merchant_test_2",
    "items": [{"id": "p2", "name": "Bunny Chow", "price": 65.00, "qty": 1}],
    "delivery_area": "Soweto",
    "customer_email": "customer2@example.com"
  }')
OID2=$(echo "$ORDER2" | python -c "import sys, json; print(json.load(sys.stdin)['order_id'])")
PID2=$(echo "$ORDER2" | python -c "import sys, json; print(json.load(sys.stdin)['payment_id'])")

CONFIRM2=$(curl -s -X POST "$API/api/orders/confirm" \
  -H "Content-Type: application/json" \
  -d "{\"order_id\": \"$OID2\", \"payment_id\": \"$PID2\"}")
echo "$CONFIRM2" | python -m json.tool

RIDER2_ID=$(echo "$CONFIRM2" | python -c "import sys, json; d=json.load(sys.stdin); print(d.get('dispatch',{}).get('rider',{}).get('id',''))")
echo "  → Assigned rider: $RIDER2_ID"

if [ "$RIDER1_ID" != "$RIDER2_ID" ]; then
  echo "  ✅ Different rider assigned (load balancing works)"
else
  echo "  ❌ Same rider assigned — load balancing FAILED"
fi

echo ""
echo "=== 5. Complete ORDER 1 → rider $RIDER1_ID returns to AVAILABLE ==="
curl -s -X POST "$API/api/riders/$RIDER1_ID/complete?order_id=$OID1" | python -m json.tool

echo ""
echo "=== 6. Riders after completion ==="
curl -s "$API/api/riders/zone/Soweto" | python -m json.tool

echo ""
echo "=== 7. Create + confirm ORDER 3 (should reuse freed rider) ==="
ORDER3=$(curl -s -X POST "$API/api/remotepay/create-payment" \
  -H "Content-Type: application/json" \
  -d '{
    "shop_id": "shop_test_3",
    "merchant_id": "merchant_test_3",
    "items": [{"id": "p3", "name": "Bunny Chow", "price": 65.00, "qty": 1}],
    "delivery_area": "Soweto",
    "customer_email": "customer3@example.com"
  }')
OID3=$(echo "$ORDER3" | python -c "import sys, json; print(json.load(sys.stdin)['order_id'])")
PID3=$(echo "$ORDER3" | python -c "import sys, json; print(json.load(sys.stdin)['payment_id'])")

curl -s -X POST "$API/api/orders/confirm" \
  -H "Content-Type: application/json" \
  -d "{\"order_id\": \"$OID3\", \"payment_id\": \"$PID3\"}" | python -m json.tool

echo ""
echo "✅ Dispatch test complete."
