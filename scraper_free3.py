import requests, json, time, urllib.parse

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
  ("food", "shisanyama Roodepoort"),
  ("education", "driving school Roodepoort"),
]

listings = []
seen = set()

for cat, q in SEARCHES:
    print(f"Searching: {q} ...")
    try:
        url = f"https://photon.komoot.io/api/?q={urllib.parse.quote(q)}&limit=20"
        r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
        print(f"  Status: {r.status_code}")
        if r.status_code != 200:
            print(f"  ❌ {r.text[:200]}")
            continue
        data = r.json()
        feats = data.get("features", [])
        print(f"  Found: {len(feats)}")
        for f in feats:
            props = f.get("properties", {})
            name = props.get("name")
            if not name or name in seen: continue
            seen.add(name)
            coords = f.get("geometry", {}).get("coordinates", [0,0])
            # Build address
            addr_parts = [props.get("street",""), props.get("housenumber",""), props.get("city",""), props.get("district","")]
            address = " ".join([x for x in addr_parts if x]).strip() or props.get("name","")
            listings.append({
                "name": name,
                "category": cat,
                "area": "Roodepoort",
                "address": address,
                "phone": props.get("phone","") if "phone" in props else "",
                "website": "",
                "rating": None,
                "reviews": 0,
                "lat": coords[1] if len(coords)>1 else None,
                "lng": coords[0] if len(coords)>0 else None,
                "source": "photon",
                "verified": False
            })
            print(f"  ✅ {name} - {props.get('city','')} / {props.get('type','')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    time.sleep(0.5)

with open("listings.json", "w") as f:
    json.dump(listings, f, indent=2)
print(f"\n🔥 DONE: {len(listings)} REAL businesses")
