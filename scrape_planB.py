import json, sys, time, urllib.request, urllib.parse

PROVINCE = sys.argv[1] if len(sys.argv)>1 else "KwaZulu-Natal"
CITY = sys.argv[2] if len(sys.argv)>2 else "Durban"

METRO_MAP = {
  "Durban": "eThekwini", "Umhlanga": "eThekwini",
  "Gqeberha": "Nelson Mandela Bay", "East London": "Buffalo City",
  "Bloemfontein": "Mangaung", "Polokwane": "Capricorn",
  "Nelspruit": "Ehlanzeni", "Rustenburg": "Bojanala", "Kimberley": "Frances Baard",
  "Cape Town": "City of Cape Town", "Stellenbosch": "Cape Winelands",
}

# Nominatim - search by category + city, 1 query per category, but tiny + fast
CATEGORIES = ["restaurant", "pharmacy", "supermarket", "cafe", "hotel", "hairdresser", "car repair"]

def fetch_nominatim(query):
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=30&addressdetails=1"
    req = urllib.request.Request(url, headers={"User-Agent":"Ubernie-SA/1.0 (business directory)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ⚠️ {query} failed: {e}")
        return []

with open('listings.json') as f: data=json.load(f)
existing = set((x.get('name','').lower(), x.get('area','').lower()) for x in data)
print(f"Before: {len(data)} | Target: {CITY}, {PROVINCE}")

new = 0
for cat in CATEGORIES:
    q = f"{cat} in {CITY}, South Africa"
    print(f"  🔍 {q}...")
    results = fetch_nominatim(q)
    print(f"     -> {len(results)} found")
    for r in results:
        name = r.get('display_name','').split(',')[0].strip()
        if not name or len(name)<3: continue
        key = (name.lower(), CITY.lower())
        if key in existing: continue
        existing.add(key)
        addr = r.get('display_name','')
        data.append({
            "name": name, "category": cat, "area": CITY, "address": addr,
            "phone": "", "website": "",
            "rating": 4.5, "reviews": 10,
            "lat": float(r.get('lat',0)), "lng": float(r.get('lon',0)),
            "source": "nominatim", "verified": False,
            "province": PROVINCE, "metro": METRO_MAP.get(CITY, CITY), "suburb": CITY,
            "audit": {"score":42,"has_phone":False,"has_website":False,"has_rating":False,"has_photos":False,"has_hours":False,"has_whatsapp":False,"missing":["phone","website","photos","opening_hours","whatsapp_button"],"upsell_value":1800,"status":"UNCLAIMED","claimed":False}
        })
        new += 1
    time.sleep(1.2) # Nominatim wants 1 sec between calls - respect it

with open('listings.json','w') as f: json.dump(data,f,indent=2)
from collections import Counter
print(f"\n✅ DONE {CITY}: +{new} new, Total {len(data)}")
print("PROVINCES:", Counter([d.get('province') for d in data]))
