import requests, json, os, time
API_KEY = os.getenv("GOOGLE_PLACES_KEY", "PASTE_YOUR_KEY_HERE")
LAT, LNG = -26.125, 27.875
RADIUS = 15000
SEARCHES = [
  ("day-care", "day care creche kindergarten Roodepoort"),
  ("day-care", "nursery school Roodepoort"),
  ("automotive", "car repair Roodepoort"),
  ("automotive", "car wash Roodepoort"),
  ("automotive", "car dealer Roodepoort"),
  ("property", "estate agent Roodepoort"),
  ("beauty", "beauty salon Roodepoort"),
  ("beauty", "barber Roodepoort"),
  ("beauty", "hair salon Roodepoort"),
  ("food", "restaurant Roodepoort"),
  ("food", "takeaway Roodepoort"),
  ("food", "shisanyama Roodepoort"),
  ("grocery", "supermarket Roodepoort"),
  ("grocery", "butchery Roodepoort"),
  ("health", "pharmacy Roodepoort"),
  ("health", "clinic Roodepoort"),
  ("health", "dentist Roodepoort"),
  ("education", "school Roodepoort"),
  ("education", "driving school Roodepoort"),
  ("home-services", "plumber Roodepoort"),
  ("home-services", "electrician Roodepoort"),
  ("fashion", "clothing store Roodepoort"),
  ("electronics", "cellphone repair Roodepoort"),
  ("events", "event venue Roodepoort"),
  ("transport", "taxi rank Roodepoort"),
  ("pets", "veterinary Roodepoort"),
  ("fitness", "gym Roodepoort"),
  ("liquor", "bottle store Roodepoort"),
  ("accommodation", "guesthouse Roodepoort"),
]
def get_details(place_id):
    url = "https://places.googleapis.com/v1/places/" + place_id
    headers = {"X-Goog-Api-Key": API_KEY, "X-Goog-FieldMask": "displayName,formattedAddress,internationalPhoneNumber,rating,userRatingCount,regularOpeningHours,websiteUri,location"}
    r = requests.get(url, headers=headers, timeout=20)
    return r.json() if r.status_code == 200 else {}
all_listings = []
seen = set()
for cat, keyword in SEARCHES:
    print(f"Searching: {keyword} ...")
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {"X-Goog-Api-Key": API_KEY, "X-Goog-FieldMask": "places.id,places.displayName"}
    body = {"textQuery": keyword, "locationBias": {"circle": {"center": {"latitude": LAT, "longitude": LNG}, "radius": RADIUS}}, "maxResultCount": 20}
    r = requests.post(url, headers=headers, json=body, timeout=20)
    if r.status_code != 200:
        print(f"❌ {keyword}: {r.text[:300]}")
        continue
    places = r.json().get("places", [])
    for p in places:
        pid = p["id"]
        if pid in seen: continue
        seen.add(pid)
        d = get_details(pid)
        name = d.get("displayName", {}).get("text", "")
        if not name: continue
        all_listings.append({
            "name": name, "category": cat, "area": "Roodepoort",
            "address": d.get("formattedAddress", ""),
            "phone": d.get("internationalPhoneNumber", ""),
            "website": d.get("websiteUri", ""),
            "rating": d.get("rating"), "reviews": d.get("userRatingCount", 0),
            "hours": d.get("regularOpeningHours", {}).get("weekdayDescriptions", []),
            "lat": d.get("location", {}).get("latitude"),
            "lng": d.get("location", {}).get("longitude"),
            "place_id": pid, "source": "google_places", "verified": False
        })
        print(f"  ✅ {name} - {d.get('rating')}⭐ ({d.get('userRatingCount',0)} reviews)")
    time.sleep(0.5)
with open("listings.json", "w") as f:
    json.dump(all_listings, f, indent=2)
print(f"\n🔥 DONE: {len(all_listings)} REAL businesses saved to listings.json - NO DEMO")
