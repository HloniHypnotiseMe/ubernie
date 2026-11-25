import requests, json, time, urllib.parse

TOWNS = ["Roodepoort","Randburg","Sandton","Fourways","Soweto","Johannesburg","Florida","Wilgeheuwel","Honeydew","Ruimsig","Northcliff","Krugersdorp","Centurion","Pretoria","Midrand","Kempton Park","Germiston","Benoni","Boksburg","Alberton","Edenvale"]

# (category, keyword)
KEYWORDS = [
  ("health","pharmacy"), ("health","clinic"), ("health","dentist"), ("health","doctor"),
  ("food","restaurant"), ("food","shisanyama"), ("food","takeaway"), ("food","pizza"), ("food","kota"),
  ("grocery","supermarket"), ("grocery","butchery"), ("grocery","spaza"),
  ("education","school"), ("education","college"), ("day-care","creche"), ("day-care","daycare"),
  ("beauty","hair salon"), ("beauty","barber"), ("beauty","nail salon"), ("beauty","beauty salon"),
  ("automotive","car wash"), ("automotive","car repair"), ("automotive","tyre"), ("automotive","mechanic"),
  ("fitness","gym"), ("fitness","yoga"),
  ("property","estate agent"), ("property","property"),
  ("liquor","bottle store"), ("liquor","liquor store"),
  ("accommodation","guest house"), ("accommodation","hotel"), ("accommodation","lodge"),
  ("pets","veterinary"), ("pets","pet shop"),
  ("electronics","cellphone repair"), ("electronics","computer repair"),
  ("fashion","clothing store"), ("fashion","boutique"),
  ("services","laundromat"), ("services","printing"), ("services","funeral"),
]

listings = []
seen = set()

# Load old Roodepoort ones so we don't lose them
try:
    with open("listings.json") as f:
        old = json.load(f)
        for x in old:
            seen.add(x["name"].lower())
            listings.append(x)
    print(f"Loaded {len(old)} existing")
except: pass

for town in TOWNS:
    for cat, kw in KEYWORDS:
        q = f"{kw} {town}"
        try:
            url = f"https://photon.komoot.io/api/?q={urllib.parse.quote(q)}&limit=15"
            r = requests.get(url, timeout=25, headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code != 200: continue
            for f in r.json().get("features", []):
                props = f.get("properties", {})
                name = props.get("name")
                if not name: continue
                key = name.lower().strip()
                if key in seen: continue
                coords = f.get("geometry", {}).get("coordinates", [0,0])
                lat, lng = coords[1] if len(coords)>1 else 0, coords[0] if len(coords)>0 else 0
                # Gauteng bbox only: lat -26.85 to -25.5, lng 27.4 to 28.7
                if not (-26.85 <= lat <= -25.50 and 27.40 <= lng <= 28.70):
                    continue
                # Must be in Gauteng area - check city/state
                city = props.get("city","") or props.get("state","")
                seen.add(key)
                addr = " ".join([x for x in [props.get("street",""), props.get("housenumber",""), props.get("city",""), props.get("district","")] if x]).strip()
                listings.append({
                    "name": name, "category": cat, "area": town,
                    "address": addr or name, "phone": "", "website": "",
                    "rating": None, "reviews": 0, "lat": lat, "lng": lng,
                    "source": "photon", "verified": False
                })
            print(f"✅ {q} - total now {len(listings)}")
        except Exception as e:
            print(f"❌ {q} {e}")
        time.sleep(0.3)

# Save
with open("listings.json","w") as f:
    json.dump(listings, f, indent=2)

from collections import Counter
print(f"\n🔥 FINAL: {len(listings)} Gauteng businesses")
print(Counter([c["category"] for c in listings]))
print(Counter([c["area"] for c in listings]))
