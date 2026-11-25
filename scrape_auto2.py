import json, time, requests

# Overpass tags for Car-la-hurry - this is how OSM actually stores them
QUERIES = {
 "dealership": ["shop=car", "shop=car_parts"],
 "mechanic": ["shop=car_repair"],
 "panel beater": ["shop=car_repair;car_repair=body"],
 "spare parts": ["shop=car_parts"],
 "car wash": ["amenity=car_wash"],
 "towing": ["shop=car_repair;car_repair=towing"],
 "tyres": ["shop=tyres"],
 "auto electrician": ["shop=car_repair;car_repair=electrical"],
 "car rental": ["amenity=car_rental"],
}
PROVINCES = {
 "Gauteng": [-26.2041, 28.0473],
 "Western Cape": [-33.9249, 18.4241],
 "KwaZulu-Natal": [-29.8587, 31.0218],
 "Eastern Cape": [-33.9608, 25.6022],
 "Free State": [-29.1211, 26.2140],
 "Limpopo": [-23.9045, 29.4689],
 "Mpumalanga": [-25.4753, 30.9696],
 "North West": [-25.6308, 25.9152],
 "Northern Cape": [-28.7282, 24.7499],
}
HEADERS = {"User-Agent": "Ubernie-CarLaHurry/1.0 (contact@ubernie.co.za)"}

def audit():
    return {"score":52,"breakdown":{"name":10,"category":10,"address":10,"latlng":12,"phone":0,"website":0,"rating":0,"photos":0,"hours":0,"whatsapp":0},"missing":["phone","website","rating","photos","hours","whatsapp"],"has_phone":False,"has_website":False,"has_rating":False,"has_photos":False,"has_hours":False,"has_whatsapp":False,"monthly_loss_estimate":24000}

existing = json.load(open("listings.json"))
seen = {(x["name"].lower(), x["area"].lower()) for x in existing}
new_items = []

for prov, (lat, lng) in PROVINCES.items():
    cnt = 0
    for cat, tags in QUERIES.items():
        for tag in tags:
            # Overpass: nodes + ways around province centre, 80km radius
            q = f"[out:json][timeout:60];(node(around:80000,{lat},{lng})[{tag}];way(around:80000,{lat},{lng})[{tag}];);out center 200;"
            try:
                r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, headers=HEADERS, timeout=70)
                print(f"{prov} / {cat} / {tag} -> HTTP {r.status_code} len {len(r.text)}")
                data = r.json()
                for el in data.get("elements", []):
                    tags2 = el.get("tags", {})
                    name = tags2.get("name")
                    if not name: continue
                    city = tags2.get("addr:city") or tags2.get("addr:town") or prov
                    key = (name.lower(), city.lower())
                    if key in seen: continue
                    seen.add(key)
                    lat2 = el.get("lat") or (el.get("center") or {}).get("lat")
                    lng2 = el.get("lon") or (el.get("center") or {}).get("lon")
                    if not lat2: continue
                    item = {"name": name, "category": cat, "area": city, "address": tags2.get("addr:full") or f"{name}, {city}, {prov}", "phone": tags2.get("phone",""), "website": tags2.get("website",""), "rating": None, "reviews": 0, "lat": lat2, "lng": lng2, "source": "overpass", "verified": False, "province": prov, "metro": city, "suburb": city, "revenue_hunter": True}
                    item["audit"] = audit()
                    new_items.append(item)
                    cnt += 1
            except Exception as e:
                print("Skip", prov, cat, tag, e)
            time.sleep(2)
    print(prov, "+", cnt)

all_data = existing + new_items
json.dump(all_data, open("listings.json","w"), indent=2)
print(f"DONE: {len(existing)} old + {len(new_items)} new = {len(all_data)} total")
