import requests, json, time, urllib.parse
from collections import Counter

TOWNS = ["Roodepoort","Randburg","Sandton","Fourways","Soweto","Johannesburg","Florida","Wilgeheuwel","Honeydew","Ruimsig","Northcliff","Krugersdorp","Centurion","Pretoria","Midrand","Kempton Park","Germiston","Benoni","Boksburg","Alberton","Edenvale","Diepsloot","Alexandra","Tembisa"]

KEYWORDS = [
  ("health","pharmacy"),("health","clinic"),("health","dentist"),
  ("food","restaurant"),("food","shisanyama"),("food","takeaway"),("food","pizza"),("food","kota"),
  ("grocery","supermarket"),("grocery","butchery"),
  ("education","school"),("education","college"),
  ("day-care","creche"),("day-care","daycare"),
  ("beauty","hair salon"),("beauty","barber"),("beauty","nail salon"),
  ("automotive","car wash"),("automotive","car repair"),("automotive","tyre"),
  ("fitness","gym"),
  ("property","estate agent"),
  ("liquor","bottle store"),
  ("accommodation","guest house"),("accommodation","hotel"),
  ("pets","veterinary"),
  ("electronics","cellphone repair"),
  ("fashion","clothing store"),
  ("services","laundromat"),("services","printing"),("services","funeral"),
]

def audit_business(b):
    # Audit: Check what's MISSING - This is what we upsell
    missing = []
    score = 100
    if not b.get("phone"): missing.append("phone"); score -= 20
    if not b.get("website"): missing.append("website"); score -= 25
    if not b.get("rating"): missing.append("google_rating"); score -= 15
    # Photon never has photos / hours / whatsapp - always missing = upsell opportunity
    missing.extend(["photos","opening_hours","whatsapp_button","online_booking"])
    score -= 40
    if score < 0: score = 0
    b["audit"] = {
        "score": max(0, score),
        "has_phone": bool(b.get("phone")),
        "has_website": bool(b.get("website")),
        "has_rating": bool(b.get("rating")),
        "has_photos": False,
        "has_hours": False,
        "has_whatsapp": False,
        "missing": missing,
        "upsell_value": len(missing) * 499,  # R499 per missing service
        "status": "UNCLAIMED",
        "claimed": False
    }
    return b

listings = []
seen = set()
# Keep existing
try:
    with open("listings.json") as f:
        for x in json.load(f):
            if x["name"].lower() not in seen:
                seen.add(x["name"].lower())
                listings.append(audit_business(x))
    print(f"Loaded {len(listings)} existing")
except Exception as e: print(f"No old file: {e}")

for town in TOWNS:
    for cat, kw in KEYWORDS:
        q = f"{kw} {town}"
        try:
            url = f"https://photon.komoot.io/api/?q={urllib.parse.quote(q)}&limit=15"
            r = requests.get(url, timeout=25, headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code != 200: continue
            for feat in r.json().get("features", []):
                props = feat.get("properties", {})
                name = props.get("name")
                if not name or name.lower().strip() in seen: continue
                coords = feat.get("geometry", {}).get("coordinates", [0,0])
                lat, lng = (coords[1] if len(coords)>1 else 0), (coords[0] if len(coords)>0 else 0)
                if not (-26.90 <= lat <= -25.45 and 27.35 <= lng <= 28.75): continue
                seen.add(name.lower().strip())
                addr = " ".join([x for x in [props.get("street",""), props.get("housenumber",""), props.get("city",""), props.get("district","")] if x]).strip()
                b = {"name": name, "category": cat, "area": town, "address": addr or name,
                     "phone": props.get("phone",""), "website": props.get("website","") or props.get("contact:website",""),
                     "rating": None, "reviews": 0, "lat": lat, "lng": lng, "source": "photon", "verified": False}
                listings.append(audit_business(b))
            print(f"✅ {q} - total {len(listings)}")
        except Exception as e: print(f"❌ {q} {e}")
        time.sleep(0.25)

with open("listings.json","w") as f: json.dump(listings, f, indent=2)
print(f"\n🔥 FINAL: {len(listings)} Gauteng businesses with AUDIT")
print(Counter([c["category"] for c in listings]))
print(Counter([c["area"] for c in listings]))
# Show audit sample
print("\nAUDIT SAMPLE - What we can upsell:")
for x in listings[:3]:
    print(f"  {x['name']} - Score {x['audit']['score']}/100 - Missing: {x['audit']['missing']} - Upsell R{x['audit']['upsell_value']}")
