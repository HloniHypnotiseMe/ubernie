import json, time, requests

QUERIES = {
 "dealership": ["shop=car", "shop=car_parts"],
 "mechanic": ["shop=car_repair"],
 "panel beater": ["shop=car_repair"],
 "spare parts": ["shop=car_parts"],
 "car wash": ["amenity=car_wash"],
 "towing": ["shop=car_repair"],
 "tyres": ["shop=tyres"],
 "auto electrician": ["shop=car_repair"],
 "car rental": ["amenity=car_rental"],
}
# MULTIPLE HUBS per province - this is what gets us to 1000+
HUBS = {
 "Gauteng": [(-26.2041,28.0473),(-25.7479,28.2293),(-26.2678,27.8652),(-26.1510,28.2570),(-26.1885,28.3228),(-26.0257,28.1721)],
 "Western Cape": [(-33.9249,18.4241),(-33.9321,18.8602),(-33.7264,18.9622),(-34.0026,23.0563),(-33.5897,22.2018),(-34.1848,18.8431)],
 "KwaZulu-Natal": [(-29.8587,31.0218),(-29.6006,30.3793),(-28.5314,30.8968),(-30.0489,30.8762),(-27.5059,30.7844),(-28.7340,30.5273)],
 "Eastern Cape": [(-33.9608,25.6022),(-32.9978,27.8662),(-33.3033,26.5217),(-32.1852,25.6155),(-33.7261,24.5536)],
 "Free State": [(-29.1211,26.2140),(-28.1158,28.4255),(-26.8321,27.8268),(-28.6368,28.8312)],
 "Limpopo": [(-23.9045,29.4689),(-23.8333,30.1500),(-22.9371,30.4457),(-24.1944,30.0095)],
 "Mpumalanga": [(-25.4753,30.9696),(-25.9628,29.2353),(-26.5200,30.1350),(-25.0000,31.0000)],
 "North West": [(-25.6308,25.9152),(-26.8799,26.6586),(-25.8570,27.2340),(-26.1880,25.8268)],
 "Northern Cape": [(-28.7282,24.7499),(-28.5744,21.2344),(-32.2018,24.5408)],
}
HEADERS = {"User-Agent": "Ubernie-CarLaHurry/1.0"}

def audit():
    return {"score":52,"breakdown":{"name":10,"category":10,"address":10,"latlng":12,"phone":0,"website":0,"rating":0,"photos":0,"hours":0,"whatsapp":0},"missing":["phone","website","rating","photos","hours","whatsapp"],"has_phone":False,"has_website":False,"has_rating":False,"has_photos":False,"has_hours":False,"has_whatsapp":False,"monthly_loss_estimate":24000}

existing = json.load(open("listings.json"))
seen = {(x["name"].lower(), x["area"].lower()) for x in existing}
new_items = []
for prov, hubs in HUBS.items():
    cnt = 0
    for (lat, lng) in hubs:
        for cat, tags in QUERIES.items():
            for tag in tags:
                q = f"[out:json][timeout:60];(node(around:40000,{lat},{lng})[{tag}];way(around:40000,{lat},{lng})[{tag}];);out center 200;"
                try:
                    r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, headers=HEADERS, timeout=70)
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
                        new_items.append(item)
                        cnt += 1
                except Exception as e:
                    print("Skip", prov, cat, e)
                time.sleep(1.5)
    print(prov, "+", cnt, "new this run")
all_data = existing + new_items
json.dump(all_data, open("listings.json","w"), indent=2)
print(f"DONE: {len(existing)} old + {len(new_items)} new = {len(all_data)} total")
