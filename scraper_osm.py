import requests, json, time

BBOX = "-26.20,27.80,-26.05,27.95"

# Try mirrors in order - if one is blocked, next works
MIRRORS = [
  "https://overpass.kumi.systems/api/interpreter",
  "https://overpass.private.coffee/api/interpreter",
  "https://overpass-api.de/api/interpreter",
]

# ONE query for ALL categories - way faster, no rate limit
QUERY = f"""
[out:json][timeout:60];
(
  node["amenity"~"kindergarten|childcare|restaurant|fast_food|cafe|pharmacy|clinic|doctors|dentist|school|college|driving_school|car_wash|taxi|car_rental|veterinary|events_venue"]({BBOX});
  node["shop"~"car|car_repair|beauty|hairdresser|barber|supermarket|convenience|butcher|bakery|clothes|shoes|mobile_phone|electronics|computer|pet|alcohol|hardware"]({BBOX});
  node["office"="estate_agent"]({BBOX});
  node["leisure"~"fitness_centre|sports_centre"]({BBOX});
  node["tourism"~"guest_house|hotel|hostel"]({BBOX});
  way["amenity"~"kindergarten|restaurant|school"]({BBOX});
  way["shop"~"supermarket|beauty|hairdresser"]({BBOX});
);
out center;
"""

CAT_MAP = {
  "kindergarten": "day-care", "childcare": "day-care",
  "car": "automotive", "car_repair": "automotive", "car_wash": "automotive",
  "estate_agent": "property",
  "beauty": "beauty", "hairdresser": "beauty", "barber": "beauty",
  "restaurant": "food", "fast_food": "food", "cafe": "food",
  "supermarket": "grocery", "convenience": "grocery", "butcher": "grocery", "bakery": "grocery",
  "pharmacy": "health", "clinic": "health", "doctors": "health", "dentist": "health",
  "school": "education", "college": "education", "driving_school": "education",
  "hardware": "home-services",
  "clothes": "fashion", "shoes": "fashion",
  "mobile_phone": "electronics", "electronics": "electronics", "computer": "electronics",
  "events_venue": "events",
  "taxi": "transport", "car_rental": "transport",
  "pet": "pets", "veterinary": "pets",
  "fitness_centre": "fitness", "sports_centre": "fitness",
  "alcohol": "liquor",
  "guest_house": "accommodation", "hotel": "accommodation", "hostel": "accommodation",
}

for url in MIRRORS:
    print(f"Trying {url} ...")
    try:
        r = requests.post(url, data={"data": QUERY}, timeout=70)
        print(f"Status: {r.status_code} | Length: {len(r.text)}")
        if r.status_code != 200 or len(r.text) < 100:
            print(f"Blocked/Empty, trying next mirror...")
            continue
        data = r.json()
        listings = []
        for el in data.get("elements", []):
            t = el.get("tags", {})
            name = t.get("name")
            if not name: continue
            # Find category
            cat = "other"
            for k in ["amenity","shop","office","leisure","tourism"]:
                if k in t and t[k] in CAT_MAP:
                    cat = CAT_MAP[t[k]]
                    break
            listings.append({
                "name": name, "category": cat, "area": "Roodepoort",
                "address": t.get("addr:full") or f"{t.get('addr:street','')} {t.get('addr:housenumber','')}".strip(),
                "phone": t.get("phone") or t.get("contact:phone") or "",
                "website": t.get("website") or "",
                "lat": el.get("lat") or el.get("center", {}).get("lat"),
                "lng": el.get("lon") or el.get("center", {}).get("lon"),
                "source": "openstreetmap", "verified": False, "rating": None, "reviews": 0
            })
        # Dedupe
        seen=set(); uniq=[]
        for l in listings:
            key=(l["name"].lower(), l["category"])
            if key not in seen:
                seen.add(key); uniq.append(l)
        with open("listings.json","w") as f: json.dump(uniq, f, indent=2)
        print(f"🔥 DONE: {len(uniq)} REAL businesses from {url}")
        break
    except Exception as e:
        print(f"❌ {url}: {e}")
        continue
