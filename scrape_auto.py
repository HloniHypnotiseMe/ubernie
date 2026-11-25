import json, time, requests
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
CATEGORIES = {
 "dealership": ["car dealer", "used car dealer"],
 "mechanic": ["mechanic", "car repair", "car service"],
 "panel beater": ["panel beater", "auto body shop"],
 "spare parts": ["auto parts", "spare parts"],
 "car wash": ["car wash", "car detailing"],
 "towing": ["towing service", "tow truck"],
 "tyres": ["tyre shop", "tyre fitment"],
 "auto electrician": ["auto electrician"],
 "car rental": ["car rental", "car hire"],
}
def audit_for(b):
    missing = ["phone","website","rating","photos","hours","whatsapp"]
    return {"score":52,"breakdown":{"name":10,"category":10,"address":10,"latlng":12,"phone":0,"website":0,"rating":0,"photos":0,"hours":0,"whatsapp":0},"missing":missing,"has_phone":False,"has_website":False,"has_rating":False,"has_photos":False,"has_hours":False,"has_whatsapp":False,"monthly_loss_estimate":24000}
existing = json.load(open("listings.json"))
seen = {(x["name"].lower(), x["area"].lower()) for x in existing}
new_items = []
for prov, (lat, lng) in PROVINCES.items():
    cnt = 0
    for cat, terms in CATEGORIES.items():
        for term in terms:
            if cnt >= 1000: break
            try:
                r = requests.get("https://photon.komoot.io/api/", params={"q": term, "lat": lat, "lon": lng, "limit": 100}, timeout=20)
                for f in r.json().get("features", []):
                    p = f.get("properties", {})
                    name = p.get("name")
                    if not name: continue
                    city = p.get("city") or p.get("town") or prov
                    key = (name.lower(), city.lower())
                    if key in seen: continue
                    seen.add(key)
                    item = {"name": name, "category": cat, "area": city, "address": p.get("street") or f"{name}, {city}, {prov}", "phone": "", "website": "", "rating": None, "reviews": 0, "lat": f["geometry"]["coordinates"][1], "lng": f["geometry"]["coordinates"][0], "source": "photon", "verified": False, "province": prov, "metro": city, "suburb": city, "revenue_hunter": True}
                    item["audit"] = audit_for(item)
                    new_items.append(item)
                    cnt += 1
            except Exception as e:
                print("Skip", term, prov, e)
            time.sleep(0.5)
    print(prov, "+", cnt)
all_data = existing + new_items
json.dump(all_data, open("listings.json","w"), indent=2)
print(f"DONE: {len(existing)} old + {len(new_items)} new = {len(all_data)} total")
