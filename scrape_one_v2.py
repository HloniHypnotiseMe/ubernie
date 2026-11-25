import json, sys, time, urllib.request, random

PROVINCE = sys.argv[1] if len(sys.argv)>1 else "KwaZulu-Natal"
CITY = sys.argv[2] if len(sys.argv)>2 else None

CITIES = {
  "Western Cape": [("Cape Town", -33.9249, 18.4241, "City of Cape Town"), ("Stellenbosch", -33.9321, 18.8602, "Cape Winelands")],
  "KwaZulu-Natal": [("Durban", -29.8587, 31.0218, "eThekwini"), ("Umhlanga", -29.7250, 31.0864, "eThekwini")],
  "Eastern Cape": [("Gqeberha", -33.9600, 25.6200, "Nelson Mandela Bay")],
  "Free State": [("Bloemfontein", -29.1200, 26.2100, "Mangaung")],
  "Limpopo": [("Polokwane", -23.9000, 29.4500, "Capricorn")],
  "Mpumalanga": [("Nelspruit", -25.4600, 30.9800, "Ehlanzeni")],
  "North West": [("Rustenburg", -25.6500, 27.2400, "Bojanala")],
  "Northern Cape": [("Kimberley", -28.7300, 24.7600, "Frances Baard")],
}

# Mirrors - if one is down, try next
MIRRORS = [
  "https://overpass-api.de/api/interpreter",
  "https://overpass.kumi.systems/api/interpreter",
  "https://overpass.private.coffee/api/interpreter",
]

def fetch_one_city(lat, lon):
    # ONE query for ALL categories - not 8 queries
    # Smaller radius 5000m, limit 100 total - much lighter
    q = f"""[out:json][timeout:30];
(
  node["amenity"~"restaurant|cafe|pharmacy|fast_food"](around:5000,{lat},{lon});
  node["shop"~"supermarket|hairdresser|beauty"](around:5000,{lat},{lon});
  node["tourism"~"hotel|guest_house|hostel"](around:5000,{lat},{lon});
  node["craft"~"car_repair"](around:5000,{lat},{lon});
);
out 100;"""
    for attempt in range(3):
        url = MIRRORS[attempt % len(MIRRORS)]
        print(f"  Trying {url.split('/')[2]} (attempt {attempt+1})...")
        try:
            req = urllib.request.Request(url, data=q.encode(), headers={"User-Agent":"Ubernie-SA/1.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                els = json.loads(r.read())["elements"]
                print(f"  ✅ Got {len(els)} places")
                return els
        except Exception as e:
            print(f"  ⚠️ Failed: {e}")
            time.sleep(5 + attempt*5) # Back off: 5s, 10s, 15s
    return []

with open('listings.json') as f: data=json.load(f)
existing = set((x.get('name','').lower(), x.get('area','').lower()) for x in data)
print(f"Before: {len(data)}")

targets = CITIES.get(PROVINCE, [])
if CITY:
    targets = [t for t in targets if t[0].lower()==CITY.lower()]
    if not targets:
        print(f"City {CITY} not found in {PROVINCE}")
        sys.exit()

new = 0
for city, lat, lon, metro in targets:
    print(f"\n📍 {city}, {PROVINCE}...")
    els = fetch_one_city(lat, lon)
    for el in els:
        tags = el.get('tags',{})
        name = tags.get('name')
        if not name: continue
        key = (name.lower(), city.lower())
        if key in existing: continue
        existing.add(key)
        # Map category
        cat = tags.get('amenity') or tags.get('shop') or tags.get('tourism') or tags.get('craft') or 'business'
        if cat in ('fast_food',): cat='restaurant'
        data.append({
            "name": name, "category": cat, "area": city, "address": tags.get('addr:street','') + ", " + city,
            "phone": tags.get('phone',''), "website": tags.get('website',''),
            "rating": 4.5, "reviews": 10, "lat": el.get('lat'), "lng": el.get('lon'),
            "source": "osm", "verified": False,
            "province": PROVINCE, "metro": metro, "suburb": city,
            "audit": {"score":42,"has_phone":bool(tags.get('phone')),"has_website":bool(tags.get('website')),"has_rating":False,"has_photos":False,"has_hours":False,"has_whatsapp":False,"missing":["website","photos","opening_hours","whatsapp_button"],"upsell_value":1800,"status":"UNCLAIMED","claimed":False}
        })
        new += 1
    print(f"  +{new} new so far")
    print(f"  😴 Sleeping 15s before next city - don't hammer Overpass...")
    time.sleep(15)

with open('listings.json','w') as f: json.dump(data,f,indent=2)
from collections import Counter
print(f"\n✅ DONE {PROVINCE}: +{new} new, Total {len(data)}")
print("PROVINCES:", Counter([d.get('province') for d in data]))
