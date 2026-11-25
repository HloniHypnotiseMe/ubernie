import json

with open("listings.json") as f:
    data = json.load(f)

print(f"Before: {len(data)}")

cleaned = []
for x in data:
    lat = x.get("lat") or 0
    lng = x.get("lng") or 0
    # Roodepoort bbox only
    if not (-26.30 <= lat <= -25.95 and 27.75 <= lng <= 28.05):
        continue
    # Remove generic junk names
    if x["name"].lower() in ["restaurants","barber","car wash","barber net","school hall","nursery substation","restaurants","the gym","bottle store","bottle store"]:
        continue
    # Remove non-SA addresses
    addr = (x.get("address") or "").lower()
    if any(bad in addr for bad in ["london","new york","dublin","ottawa","toronto","seattle","sheffield","maidenhead","edinburgh","paris","berlin"]):
        continue
    cleaned.append(x)

# Sort by category
cleaned = sorted(cleaned, key=lambda z: (z["category"], z["name"]))

with open("listings.json","w") as f:
    json.dump(cleaned, f, indent=2)

print(f"After clean: {len(cleaned)} REAL Roodepoort businesses")
from collections import Counter
print(Counter([c["category"] for c in cleaned]))
for c in cleaned:
    print(f"  ✅ {c['name']} - {c['category']} - {c['address'][:50]}")
