import json

# Real rubric - 100 points total
WEIGHTS = {
  "name": 10, "category": 10, "address": 10, "latlng": 12,
  "phone": 15, "website": 15, "rating": 10,
  "photos": 8, "hours": 5, "whatsapp": 5
}
# R-loss per missing item - this is Revenue Hunter math
LOSS = {"phone": 8500, "website": 5200, "photos": 4300, "hours": 1200, "whatsapp": 2800, "rating": 2000}

with open('listings.json') as f: data=json.load(f)

for d in data:
    breakdown = {}
    score = 0
    missing = []
    loss = 0
    # Checks
    checks = {
      "name": bool(d.get("name")),
      "category": bool(d.get("category")),
      "address": bool(d.get("address")),
      "latlng": bool(d.get("lat") and d.get("lng")),
      "phone": bool(d.get("phone")),
      "website": bool(d.get("website")),
      "rating": bool(d.get("rating") and d.get("rating")>0 and d.get("reviews",0)>0),
      "photos": bool(d.get("photos") or d.get("photo_url")),
      "hours": bool(d.get("hours") or d.get("opening_hours")),
      "whatsapp": bool(d.get("whatsapp") or d.get("whatsapp_number")),
    }
    for k, has in checks.items():
        if has:
            score += WEIGHTS[k]
            breakdown[k] = WEIGHTS[k]
        else:
            breakdown[k] = 0
            if k in LOSS:
                missing.append(k)
                loss += LOSS[k]
    d["audit"] = {
      "score": score, "breakdown": breakdown, "missing": missing,
      "has_phone": checks["phone"], "has_website": checks["website"],
      "has_rating": checks["rating"], "has_photos": checks["photos"],
      "has_hours": checks["hours"], "has_whatsapp": checks["whatsapp"],
      "monthly_loss_estimate": loss,
      "upsell_value": 1800 if score < 60 else 999 if score < 80 else 499,
      "status": "UNCLAIMED", "claimed": False
    }
    d["revenue_hunter"] = {
      "score": score,
      "monthly_loss": loss,
      "top_leak": missing[0] if missing else None,
      "headline": f"Losing ~R{loss:,}/mo" if loss>0 else "Fully optimised",
      "fixes": missing
    }

with open('listings.json','w') as f: json.dump(data,f,indent=2)
from collections import Counter
print(f"Total: {len(data)}")
print("Score buckets:", Counter(["0-49" if d["audit"]["score"]<50 else "50-79" if d["audit"]["score"]<80 else "80+" for d in data]))
print("Avg loss:", sum(d["revenue_hunter"]["monthly_loss"] for d in data)//len(data))
print("Example 42 business:", [d for d in data if d["audit"]["score"]==42][0]["revenue_hunter"])
