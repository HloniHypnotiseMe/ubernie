import requests, json, time

HEADERS = {"User-Agent": "UbernieBot/1.0 (contact: ubernie@example.com)"}

SEARCHES = [
  ("health", "pharmacy Roodepoort"),
  ("health", "clinic Roodepoort"),
  ("food", "restaurant Roodepoort"),
  ("food", "takeaway Roodepoort"),
  ("grocery", "supermarket Roodepoort"),
  ("grocery", "butchery Roodepoort"),
  ("education", "school Roodepoort"),
  ("day-care", "creche Roodepoort"),
  ("day-care", "nursery school Roodepoort"),
  ("beauty", "hair salon Roodepoort"),
  ("beauty", "barber Roodepoort"),
  ("automotive", "car wash Roodepoort"),
  ("automotive", "car repair Roodepoort"),
  ("fitness", "gym Roodepoort"),
  ("property", "estate agent Roodepoort"),
  ("liquor", "bottle store Roodepoort"),
  ("accommodation", "guest house Roodepoort"),
  ("pets", "veterinary Roodepoort"),
]

listings = []
seen = set()

for cat, q in SEARCHES:
    print(f"Searching: {q} ...")
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 15, "addressdetails": 1},
            headers=HEADERS, timeout=25)
        print(f"  Status: {r.status_code} - Got {len(r.text)} chars")
        if r.status_code != 200:
            print(f"  ❌ {r.text[:200]}")
            continue
        data = r.json()
        print(f"  Found: {len(data)}")
        for item in data:
            name = item.get("display_name", "").split(",")[0].strip()
            if not name or name in seen: continue
            seen.add(name)
            listings.append({
                "name": name,
                "category": cat,
                "area": "Roodepoort",
                "address": item.get("display_name", ""),
                "phone": "",
                "website": "",
                "rating": None,
                "reviews": 0,
                "lat": float(item.get("lat", 0)),
                "lng": float(item.get("lon", 0)),
                "source": "nominatim",
                "verified": False
            })
            print(f"  ✅ {name}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    time.sleep(1.2)

with open("listings.json", "w") as f:
    json.dump(listings, f, indent=2)
print(f"\n🔥 DONE: {len(listings)} REAL businesses")
