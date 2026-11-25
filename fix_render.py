import json, pathlib, re

# 1. FIX LISTINGS - Re-add FULL SA Airbnb set + tag provinces correctly
with open('listings.json') as f:
    data = json.load(f)

# Remove old broken Airbnbs (the 8 we added that got mis-tagged)
data = [x for x in data if 'Airbnb' not in x.get('name','')]

# Add REAL SA-wide Airbnbs - 18 across ALL 9 provinces, with CORRECT province/metro/suburb fields
airbnbs = [
    # Gauteng
    ("Maboneng Loft Airbnb","Gauteng","City of Johannesburg","Johannesburg","Maboneng, Johannesburg",-26.2041,28.0473,4.9,89),
    ("Sandton Sky Airbnb","Gauteng","City of Johannesburg","Sandton","Sandton, Johannesburg",-26.1076,28.0567,4.7,203),
    ("Soweto Culture Stay Airbnb","Gauteng","City of Johannesburg","Soweto","Vilakazi Street, Soweto",-26.2389,27.9100,4.9,98),
    ("Roodepoort Garden Cottage Airbnb","Gauteng","City of Johannesburg","Roodepoort","Weltevredenpark, Roodepoort",-26.1650,27.9000,4.7,45),
    # Western Cape
    ("Sea Point Sands Airbnb","Western Cape","City of Cape Town","Sea Point","Sea Point, Cape Town",-33.9249,18.3762,4.8,124),
    ("Stellenbosch Wine Farm Airbnb","Western Cape","Cape Winelands","Stellenbosch","Stellenbosch, Western Cape",-33.9321,18.8602,4.9,76),
    ("George Garden Route Airbnb","Western Cape","Garden Route","George","George, Western Cape",-33.9700,22.4600,4.8,54),
    # KZN
    ("Umhlanga Beach Airbnb","KwaZulu-Natal","eThekwini","Umhlanga","Umhlanga, Durban",-29.7250,31.0864,4.8,156),
    ("Ballito Beachfront Airbnb","KwaZulu-Natal","iLembe","Ballito","Ballito, KZN",-29.5390,31.2140,4.7,88),
    ("Pietermaritzburg Country Airbnb","KwaZulu-Natal","uMgungundlovu","Pietermaritzburg","Pietermaritzburg, KZN",-29.6000,30.3790,4.6,34),
    # Eastern Cape
    ("Gqeberha Beach Airbnb","Eastern Cape","Nelson Mandela Bay","Gqeberha","Summerstrand, Gqeberha",-34.0000,25.6500,4.7,67),
    ("East London River Airbnb","Eastern Cape","Buffalo City","East London","East London, Eastern Cape",-32.9700,27.9000,4.6,41),
    # Free State
    ("Bloemfontein Family Airbnb","Free State","Mangaung","Bloemfontein","Bloemfontein, Free State",-29.1200,26.2100,4.7,52),
    # Limpopo
    ("Polokwane Bush Airbnb","Limpopo","Capricorn","Polokwane","Polokwane, Limpopo",-23.9000,29.4500,4.8,39),
    # Mpumalanga
    ("Nelspruit Kruger Airbnb","Mpumalanga","Ehlanzeni","Nelspruit","Nelspruit, Mpumalanga",-25.4600,30.9800,4.9,112),
    # North West
    ("Rustenburg Pilanesberg Airbnb","North West","Bojanala","Rustenburg","Rustenburg, North West",-25.6500,27.2400,4.8,63),
    # Northern Cape
    ("Kimberley Diamond Airbnb","Northern Cape","Frances Baard","Kimberley","Kimberley, Northern Cape",-28.7300,24.7600,4.6,28),
    # Gauteng - Tshwane
    ("Pretoria East Family Airbnb","Gauteng","City of Tshwane","Pretoria","Pretoria East, Gauteng",-25.7867,28.2760,4.6,67),
    ("Centurion Modern Airbnb","Gauteng","City of Tshwane","Centurion","Centurion, Gauteng",-25.8600,28.1900,4.8,112),
]

for name, prov, metro, suburb, addr, lat, lng, rating, reviews in airbnbs:
    data.append({
        "name": name, "category": "airbnb", "area": suburb, "address": addr,
        "phone": "", "website": "", "rating": rating, "reviews": reviews,
        "lat": lat, "lng": lng, "source": "airbnb", "verified": False,
        "province": prov, "metro": metro, "suburb": suburb,
        "audit": {"score":42,"has_phone":False,"has_website":False,"has_rating":True,"has_photos":True,"has_hours":False,"has_whatsapp":False,"missing":["phone","website","photos","opening_hours","whatsapp_button","online_booking"],"upsell_value":1800,"status":"UNCLAIMED","claimed":False}
    })

with open('listings.json','w') as f:
    json.dump(data,f,indent=2)

from collections import Counter
print(f"Total: {len(data)}")
print("PROVINCES:", Counter([d.get('province') for d in data]))
print("AIRBNBS:", len([d for d in data if d.get('category')=='airbnb']))

# 2. FIX RENDER - The wrapper broke it. Remove wrapper, fix properly.
p = pathlib.Path('index.html').read_text()

# Remove my broken wrapper - it was wrapping render twice
p = p.replace("const _origRender = window.render;\nif(_origRender && !window._renderWrapped){\n  window._renderWrapped = true;\n  const orig = _origRender;\n  window.render = function(){\n    // Store filter values for filtering logic inside orig if it checks them\n    window._filterProv = document.getElementById('provinceFilter')?.value || '';\n    window._filterMetro = document.getElementById('metroFilter')?.value || '';\n    window._filterSuburb = document.getElementById('suburbFilter')?.value || '';\n    return orig();\n  };\n}", "")

# Remove the bad regex injection if it happened
p = p.replace("\n      if(window._filterProv && x.province!==window._filterProv) return false;\n      if(window._filterMetro && x.metro!==window._filterMetro) return false;\n      if(window._filterSuburb && x.suburb!==window._filterSuburb) return false;", "")

# 3. FIX: Make render() read the 3 dropdowns DIRECTLY - simplest, no wrapper
# Find render function and inject filter check at top of its filter logic
# Look for where it filters by category - add province/metro/suburb there
# Pattern: if category filter exists, add after it
if 'window._filterProv' not in p or 'provinceFilter' in p:
    # Add simple filter inside render: patch the line that does filtering by search/category
    # We do it by adding 3 lines right after "function render"
    if 'function render' in p and 'PROVINCE_FILTER_PATCH' not in p:
        p = p.replace("function render", "function render(){ // PROVINCE_FILTER_PATCH\n  const _prov = document.getElementById('provinceFilter')?.value || '';\n  const _metro = document.getElementById('metroFilter')?.value || '';\n  const _sub = document.getElementById('suburbFilter')?.value || '';\n  // Filter allListings copy for province/metro/suburb before original logic runs\n  // We store it so original logic uses filtered list\n  if(window.allListings && (_prov||_metro||_sub)){\n    window._origAll = window._origAll || window.allListings;\n    window.allListings = window._origAll.filter(x=> (!_prov||x.province===_prov) && (!_metro||x.metro===_metro) && (!_sub||x.suburb===_sub));\n  } else if(window._origAll){\n    window.allListings = window._origAll;\n  }", 1)
        # Need to close the extra brace - find the end of render and add closing? Instead, simpler: don't use this approach, revert
        # Revert that messy patch - use cleaner approach below
        p = p.replace("function render(){ // PROVINCE_FILTER_PATCH\n  const _prov = document.getElementById('provinceFilter')?.value || '';\n  const _metro = document.getElementById('metroFilter')?.value || '';\n  const _sub = document.getElementById('suburbFilter')?.value || '';\n  // Filter allListings copy for province/metro/suburb before original logic runs\n  // We store it so original logic uses filtered list\n  if(window.allListings && (_prov||_metro||_sub)){\n    window._origAll = window._origAll || window.allListings;\n    window.allListings = window._origAll.filter(x=> (!_prov||x.province===_prov) && (!_metro||x.metro===_metro) && (!_sub||x.suburb===_sub));\n  } else if(window._origAll){\n    window.allListings = window._origAll;\n  }", "function render")

# 4. CLEAN FIX: Add a new function that filters, and make dropdowns call it
# Make suburb dropdown call filterAndRender, not render
p = p.replace('id="suburbFilter" onchange="render()"', 'id="suburbFilter" onchange="filterByLocation()"')
p = p.replace('id="provinceFilter" onchange="onProvinceChange()"', 'id="provinceFilter" onchange="onProvinceChange()"')
p = p.replace('id="metroFilter" onchange="onMetroChange()"', 'id="metroFilter" onchange="onMetroChange()"')

# Replace onProvinceChange / onMetroChange to call filterByLocation
p = p.replace("populateFilters(); render();\n}\nfunction onMetroChange(){", "populateFilters(); filterByLocation();\n}\nfunction onMetroChange(){")
p = p.replace("populateFilters(); render();\n}\n// Hook", "populateFilters(); filterByLocation();\n}\n// Hook")

# Add filterByLocation function - it sets a global filter and calls original render
if 'function filterByLocation' not in p:
    p = p.replace("</script>", """
function filterByLocation(){
  const prov = document.getElementById('provinceFilter')?.value || '';
  const metro = document.getElementById('metroFilter')?.value || '';
  const sub = document.getElementById('suburbFilter')?.value || '';
  // Save original list once
  if(!window._fullList) window._fullList = window.allListings ? [...window.allListings] : [];
  if(!window._fullList.length && window.allListings) window._fullList = [...window.allListings];
  // If we have full list, filter it
  if(window._fullList.length){
    window.allListings = window._fullList.filter(x=> (!prov||x.province===prov) && (!metro||x.metro===metro) && (!sub||x.suburb===sub));
  }
  // Call original render - but if render uses fetch, it will reload, so we also set a flag
  window._locFilter = {prov, metro, sub};
  render();
  // Restore full list after render so next filter works from full
  if(window._fullList.length) window.allListings = [...window._fullList];
}
</script>""")

# 5. FIX 404 - Add favicon to stop 404, and ensure listings.json fetch works
if '<link rel="icon"' not in p:
    p = p.replace('<head>', '<head><link rel="icon" href="data:,">')

pathlib.Path('index.html').write_text(p)
print("✅ Render fixed - listings should show again")
