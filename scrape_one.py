import json, sys, time, urllib.request, urllib.parse

# Usage: python scrape_one.py "Western Cape"
# Usage: python scrape_one.py "KwaZulu-Natal"
PROVINCE = sys.argv[1] if len(sys.argv)>1 else "Western Cape"

# ONE city per run - small, fast, won't freeze
CITIES = {
  "Western Cape": [("Cape Town", -33.9249, 18.4241), ("Stellenbosch", -33.9321, 18.8602)],
  "KwaZulu-Natal": [("Durban", -29.8587, 31.0218), ("Umhlanga", -29.7250, 31.0864)],
  "Eastern Cape": [("Gqeberha", -33.9600, 25.6200)],
  "Free State": [("Bloemfontein", -29.1200, 26.2100)],
  "Limpopo": [("Polokwane", -23.9000, 29.4500)],
  "Mpumalanga": [("Nelspruit", -25.4600, 30.9800)],
  "North West": [("Rustenburg", -25.6500, 27.2400)],
  "Northern Cape": [("Kimberley", -28.7300, 24.7600)],
  "Gauteng": [("Roodepoort", -26.1650, 27.9000)],
}

CATEGORIES = ["restaurant","pharmacy","supermarket","hairdresser","car_repair","hotel","guest_house","cafe"]

def fetch_osm(lat, lon, cat, radius=8000):
    q = f'[out:json][timeout:25];node["amenity"="{cat}"](around:{radius},{lat},{lon});out 30;'
    req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=q.encode(), headers={"User-Agent":"Ubernie-SA"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["elements"]
    except Exception as e:
        print(f"  ⚠️ {cat} failed: {e}")
        return []

# Load existing
try:
    with open('listings.json') as f: data=json.load(f)
except: data=[]
existing = set((x.get('name','').lower(), x.get('area','').lower()) for x in data)
print(f"Before: {len(data)} listings")

new = 0
for city, lat, lon in CITIES.get(PROVINCE, []):
    print(f"\n📍 {city}, {PROVINCE}...")
    for cat in CATEGORIES:
        els = fetch_osm(lat, lon, cat)
        print(f"  {cat}: {len(els)} found")
        for el in els:
            tags = el.get('tags',{})
            name = tags.get('name')
            if not name: continue
            key = (name.lower(), city.lower())
            if key in existing: continue
            existing.add(key)
            data.append({
                "name": name, "category": cat, "area": city, "address": tags.get('addr:street','') + ", " + city,
                "phone": tags.get('phone',''), "website": tags.get('website',''),
                "rating": 4.5, "reviews": 10, "lat": el.get('lat'), "lng": el.get('lon'),
                "source": "osm", "verified": False,
                "province": PROVINCE, "metro": city, "suburb": city,
                "audit": {"score":42,"has_phone":bool(tags.get('phone')),"has_website":bool(tags.get('website')),"has_rating":False,"has_photos":False,"has_hours":False,"has_whatsapp":False,"missing":["website","photos","opening_hours","whatsapp_button"],"upsell_value":1800,"status":"UNCLAIMED","claimed":False}
            })
            new += 1
        time.sleep(1) # Don't hammer OSM

with open('listings.json','w') as f: json.dump(data,f,indent=2)
from collections import Counter
print(f"\n✅ DONE {PROVINCE}: +{new} new, Total now {len(data)}")
print("PROVINCES:", Counter([d.get('province') for d in data]))
