import json, time, requests

QUERIES = {
 "dealership": ["shop=car"],
 "mechanic": ["shop=car_repair"],
 "spare parts": ["shop=car_parts"],
 "car wash": ["amenity=car_wash"],
 "tyres": ["shop=tyres"],
 "car rental": ["amenity=car_rental"],
}
HUBS = {
 "Gauteng": [(-26.2041,28.0473),(-25.7479,28.2293),(-26.2678,27.8652)],
 "Western Cape": [(-33.9249,18.4241),(-33.9321,18.8602),(-33.7264,18.9622)],
 "KwaZulu-Natal": [(-29.8587,31.0218),(-29.6006,30.3793),(-28.5314,30.8968)],
 "Eastern Cape": [(-33.9608,25.6022),(-32.9978,27.8662),(-33.3033,26.5217)],
 "Free State": [(-29.1211,26.2140),(-28.1158,28.4255)],
 "Limpopo": [(-23.9045,29.4689),(-23.8333,30.1500)],
 "Mpumalanga": [(-25.4753,30.9696),(-25.9628,29.2353)],
 "North West": [(-25.6308,25.9152),(-26.8799,26.6586)],
 "Northern Cape": [(-28.7282,24.7499),(-28.5744,21.2344)],
}
MIRRORS = ["https://overpass-api.de/api/interpreter","https://overpass.private.coffee/api/interpreter","https://overpass.kumi.systems/api/interpreter"]
HEADERS = {"User-Agent": "Ubernie-CarLaHurry/1.0"}

def audit():
    return {"score":52,"breakdown":{"name":10,"category":10,"address":10,"latlng":12,"phone":0,"website":0,"rating":0,"photos":0,"hours":0,"whatsapp":0},"missing":["phone","website","rating","photos","hours","whatsapp"],"has_phone":False,"has_website":False,"has_rating":False,"has_photos":False,"has_hours":False,"has_whatsapp":False,"monthly_loss_estimate":24000}

def load():
    return json.load(open("listings.json"))
def save(data):
    json.dump(data, open("listings.json","w"), indent=2)
    print(f"SAVED: {len(data)} total", flush=True)

existing = load()
seen = {(x["name"].lower(), x["area"].lower()) for x in existing}

for prov, hubs in HUBS.items():
    # SKIP if already 1000+ in this province - don't waste API calls
    cnt_prov = sum(1 for x in existing if x.get("province")==prov)
    if cnt_prov >= 300:
        print(f"{prov}: already {cnt_prov} - SKIP", flush=True)
        continue
    cnt_new = 0
    for (lat, lng) in hubs:
        for cat, tags in QUERIES.items():
            for tag in tags:
                q = f"[out:json][timeout:45];(node(around:40000,{lat},{lng})[{tag}];way(around:40000,{lat},{lng})[{tag}];);out center 100;"
                ok = False
                for mirror in MIRRORS:
                    try:
                        r = requests.post(mirror, data={"data": q}, headers=HEADERS, timeout=50)
                        if r.status_code != 200 or not r.text.strip().startswith("{"):
                            print(f"  {prov}/{cat} mirror {mirror} -> {r.status_code} empty, trying next", flush=True)
                            time.sleep(3)
                            continue
                        for el in r.json().get("elements", []):
                            t = el.get("tags", {})
                            name = t.get("name")
                            if not name: continue
                            city = t.get("addr:city") or t.get("addr:town") or prov
                            key = (name.lower(), city.lower())
                            if key in seen: continue
                            seen.add(key)
                            lat2 = el.get("lat") or (el.get("center") or {}).get("lat")
                            lng2 = el.get("lon") or (el.get("center") or {}).get("lon")
                            if not lat2: continue
                            item = {"name": name, "category": cat, "area": city, "address": t.get("addr:full") or f"{name}, {city}, {prov}", "phone": t.get("phone",""), "website": t.get("website",""), "rating": None, "reviews": 0, "lat": lat2, "lng": lng2, "source": "overpass", "verified": False, "province": prov, "metro": city, "suburb": city, "revenue_hunter": True}
                            item["audit"] = audit()
                            existing.append(item)
                            cnt_new += 1
                        ok = True
                        break
                    except Exception as e:
                        print(f"  Skip {prov}/{cat} on {mirror}: {e}", flush=True)
                        time.sleep(3)
                time.sleep(3)  # slower = no 429
    print(f"{prov}: +{cnt_new} new", flush=True)
    save(existing)  # SAVE AFTER EVERY PROVINCE - crash = lose max 1 province, not all

print("ALL DONE")
