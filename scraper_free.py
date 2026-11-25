import requests, json, time

# Overpass API - OpenStreetMap - FREE, NO KEY
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Roodepoort bbox: south, west, north, east
BBOX = "-26.22,27.78,-26.02,27.98"

QUERY = f"""
[out:json][timeout:60];
(
  node["amenity"~"pharmacy|clinic|dentist|restaurant|fast_food|cafe|school|kindergarten|bank|fuel|car_wash|car_repair|beauty|hairdresser|barber|gym|marketplace|bureau_de_change"]({BBOX});
  node["shop"~"supermarket|convenience|butcher|bakery|clothes|hairdresser|beauty|mobile_phone|electronics|car_repair|car|alcohol"]({BBOX});
  node["office"~"estate_agent|lawyer|accountant"]({BBOX});
  node["tourism"~"guest_house|hotel|hostel"]({BBOX});
  node["leisure"~"fitness_centre|swimming_pool"]({BBOX});
  way["amenity"~"pharmacy|clinic|dentist|restaurant|fast_food|cafe|school|kindergarten"]({BBOX});
  way["shop"~"supermarket|convenience|butcher|bakery|clothes"]({BBOX});
);
out center;
"""

print("Fetching Roodepoort businesses from OpenStreetMap...")
r = requests.post(OVERPASS_URL, data={"data": QUERY}, timeout=70)
data = r.json()
print(f"Raw nodes: {len(data.get('elements', []))}")

# Category mapping
def get_category(tags):
    a = tags.get("amenity", "")
    s = tags.get("shop", "")
    o = tags.get("office", "")
    t = tags.get("tourism", "")
    l = tags.get("leisure", "")
    if a in ["kindergarten"]: return "day-care"
    if a in ["school"]: return "education"
    if a in ["pharmacy", "clinic", "dentist"]: return "health"
    if a in ["restaurant", "fast_food", "cafe"]: return "food"
    if a in ["car_wash", "car_repair", "fuel"]: return "automotive"
    if a in ["beauty", "hairdresser", "barber"]: return "beauty"
    if a in ["gym"]: return "fitness"
    if s in ["supermarket", "convenience", "butcher", "bakery"]: return "grocery"
    if s in ["clothes"]: return "fashion"
    if s in ["mobile_phone", "electronics"]: return "electronics"
    if s in ["car_repair", "car"]: return "automotive"
    if s in ["alcohol"]: return "liquor"
    if o == "estate_agent": return "property"
    if t in ["guest_house", "hotel", "hostel"]: return "accommodation"
    if l == "fitness_centre": return "fitness"
    return "general"

listings = []
seen = set()
for el in data.get("elements", []):
    tags = el.get("tags", {})
    name = tags.get("name")
    if not name or name in seen: continue
    seen.add(name)
    lat = el.get("lat") or el.get("center", {}).get("lat")
    lng = el.get("lon") or el.get("center", {}).get("lon")
    listings.append({
        "name": name,
        "category": get_category(tags),
        "area": "Roodepoort",
        "address": tags.get("addr:full", "") or f"{tags.get('addr:street','')} {tags.get('addr:housenumber','')}".strip(),
        "phone": tags.get("phone", "") or tags.get("contact:phone", ""),
        "website": tags.get("website", "") or tags.get("contact:website", ""),
        "rating": None,
        "reviews": 0,
        "lat": lat,
        "lng": lng,
        "source": "openstreetmap",
        "verified": False
    })
    print(f"  ✅ {name} - {get_category(tags)}")

with open("listings.json", "w") as f:
    json.dump(listings, f, indent=2)

print(f"\n🔥 DONE: {len(listings)} REAL businesses saved to listings.json")
