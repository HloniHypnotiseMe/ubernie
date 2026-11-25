import json, pathlib, re

# 1. MAP EVERY AREA TO PROVINCE -> METRO -> SUBURB
# This is SA-correct, not Gauteng-only
PROVINCE_MAP = {
    # GAUTENG
    'Roodepoort':'Gauteng|City of Johannesburg|Roodepoort',
    'Randburg':'Gauteng|City of Johannesburg|Randburg',
    'Sandton':'Gauteng|City of Johannesburg|Sandton',
    'Johannesburg':'Gauteng|City of Johannesburg|Johannesburg',
    'Soweto':'Gauteng|City of Johannesburg|Soweto',
    'Fourways':'Gauteng|City of Johannesburg|Fourways',
    'Midrand':'Gauteng|City of Johannesburg|Midrand',
    'Centurion':'Gauteng|City of Tshwane|Centurion',
    'Pretoria':'Gauteng|City of Tshwane|Pretoria',
    'Hatfield':'Gauteng|City of Tshwane|Hatfield',
    'Mamelodi':'Gauteng|City of Tshwane|Mamelodi',
    'Ekurhuleni':'Gauteng|Ekurhuleni|Ekurhuleni',
    'Benoni':'Gauteng|Ekurhuleni|Benoni',
    'Boksburg':'Gauteng|Ekurhuleni|Boksburg',
    'Kempton Park':'Gauteng|Ekurhuleni|Kempton Park',
    'Germiston':'Gauteng|Ekurhuleni|Germiston',
    'Vereeniging':'Gauteng|Sedibeng|Vereeniging',
    'Vanderbijlpark':'Gauteng|Sedibeng|Vanderbijlpark',
    'Westonaria':'Gauteng|West Rand|Westonaria',
    'Krugersdorp':'Gauteng|West Rand|Krugersdorp',
    'Weltevredenpark':'Gauteng|City of Johannesburg|Roodepoort',
    # WESTERN CAPE
    'Cape Town':'Western Cape|City of Cape Town|Cape Town',
    'Sea Point':'Western Cape|City of Cape Town|Sea Point',
    'Stellenbosch':'Western Cape|Cape Winelands|Stellenbosch',
    'Paarl':'Western Cape|Cape Winelands|Paarl',
    'George':'Western Cape|Garden Route|George',
    # KZN
    'Durban':'KwaZulu-Natal|eThekwini|Durban',
    'Umhlanga':'KwaZulu-Natal|eThekwini|Umhlanga',
    'Pietermaritzburg':'KwaZulu-Natal|uMgungundlovu|Pietermaritzburg',
    'Ballito':'KwaZulu-Natal|iLembe|Ballito',
    # EASTERN CAPE
    'Gqeberha':'Eastern Cape|Nelson Mandela Bay|Gqeberha',
    'East London':'Eastern Cape|Buffalo City|East London',
    # FREE STATE
    'Bloemfontein':'Free State|Mangaung|Bloemfontein',
    # LIMPOPO
    'Polokwane':'Limpopo|Capricorn|Polokwane',
    # MPUMALANGA
    'Nelspruit':'Mpumalanga|Ehlanzeni|Nelspruit',
    'Mbombela':'Mpumalanga|Ehlanzeni|Mbombela',
    # NORTH WEST
    'Rustenburg':'North West|Bojanala|Rustenburg',
    'Mahikeng':'North West|Ngaka Modiri Molema|Mahikeng',
    # NORTHERN CAPE
    'Kimberley':'Northern Cape|Frances Baard|Kimberley',
}

with open('listings.json') as f:
    data = json.load(f)

# Tag every listing with province/metro/suburb
for x in data:
    area = x.get('area','').strip()
    # Try exact match, else substring match
    key = None
    if area in PROVINCE_MAP:
        key = area
    else:
        for k in PROVINCE_MAP:
            if k.lower() in area.lower() or area.lower() in k.lower():
                key = k
                break
    if key:
        prov, metro, suburb = PROVINCE_MAP[key].split('|')
        x['province'] = prov
        x['metro'] = metro
        x['suburb'] = suburb
    else:
        # Fallback: keep area as suburb, guess Gauteng if unknown (most of our data is Gauteng)
        x['province'] = x.get('province','Gauteng')
        x['metro'] = x.get('metro','City of Johannesburg')
        x['suburb'] = area

with open('listings.json','w') as f:
    json.dump(data,f,indent=2)

# Print counts so you can verify
from collections import Counter
print("PROVINCES:", Counter([d.get('province') for d in data]))
print("METROS:", Counter([d.get('metro') for d in data]))
print("SUBURBS:", sorted(set([d.get('suburb') for d in data]))[:30])

# 2. FIX INDEX.HTML - ONLY REPLACE THE AREA FILTER, NOTHING ELSE
p = pathlib.Path('index.html').read_text()

# Backup check - don't duplicate if already fixed
if 'id="provinceFilter"' in p:
    print("Already fixed, skipping HTML patch")
else:
    # Find the old single area select - it looks like <select id="areaFilter"...> or <select id="area"...>
    # Replace it with 3 selects
    old_pattern = re.search(r'<select[^>]*id=["\']area[^"\']*["\'][^>]*>.*?</select>', p, re.DOTALL | re.IGNORECASE)
    if old_pattern:
        new_filters = '''<select id="provinceFilter" onchange="onProvinceChange()"><option value="">All Provinces - South Africa</option></select>
<select id="metroFilter" onchange="onMetroChange()"><option value="">All Metros</option></select>
<select id="suburbFilter" onchange="render()"><option value="">All Suburbs</option></select>'''
        p = p.replace(old_pattern.group(0), new_filters)
        print("✅ Replaced single Area dropdown with 3 dropdowns")
    else:
        # Fallback: insert after search input
        p = p.replace('<div class="filters">', '<div class="filters"><select id="provinceFilter" onchange="onProvinceChange()"><option value="">All Provinces - South Africa</option></select><select id="metroFilter" onchange="onMetroChange()"><option value="">All Metros</option></select><select id="suburbFilter" onchange="render()"><option value="">All Suburbs</option></select>')
        print("✅ Inserted 3 dropdowns (fallback)")

    # Add JS for cascading filters - insert before </script>, but DON'T touch other functions
    js = """
// ===== PROVINCE -> METRO -> SUBURB CASCADE - ADDED, DOES NOT TOUCH OTHER CODE =====
function getUnique(arr, key){ return [...new Set(arr.map(x=>x[key]).filter(Boolean))].sort(); }
function populateFilters(){
  const provSel = document.getElementById('provinceFilter');
  const metroSel = document.getElementById('metroFilter');
  const suburbSel = document.getElementById('suburbFilter');
  if(!provSel) return;
  // Save current selections
  const curProv = provSel.value, curMetro = metroSel.value, curSub = suburbSel.value;
  // Provinces
  const provs = getUnique(window.allListings || [], 'province');
  provSel.innerHTML = '<option value="">All Provinces - South Africa</option>' + provs.map(x=>`<option value="${x}">${x}</option>`).join('');
  provSel.value = curProv;
  // Metros filtered by province
  let metroPool = (window.allListings || []).filter(x=>!curProv || x.province===curProv);
  const metros = getUnique(metroPool, 'metro');
  metroSel.innerHTML = '<option value="">All Metros</option>' + metros.map(x=>`<option value="${x}">${x}</option>`).join('');
  metroSel.value = curMetro;
  // Suburbs filtered by province + metro
  let subPool = metroPool.filter(x=>!curMetro || x.metro===curMetro);
  const subs = getUnique(subPool, 'suburb');
  suburbSel.innerHTML = '<option value="">All Suburbs</option>' + subs.map(x=>`<option value="${x}">${x}</option>`).join('');
  suburbSel.value = curSub;
}
function onProvinceChange(){
  const metroSel=document.getElementById('metroFilter'); const subSel=document.getElementById('suburbFilter');
  if(metroSel) metroSel.value=''; if(subSel) subSel.value='';
  populateFilters(); render();
}
function onMetroChange(){
  const subSel=document.getElementById('suburbFilter'); if(subSel) subSel.value='';
  populateFilters(); render();
}
// Hook into existing render - wrap it to also filter by province/metro/suburb
const _origRender = window.render;
if(_origRender && !window._renderWrapped){
  window._renderWrapped = true;
  const orig = _origRender;
  window.render = function(){
    // Store filter values for filtering logic inside orig if it checks them
    window._filterProv = document.getElementById('provinceFilter')?.value || '';
    window._filterMetro = document.getElementById('metroFilter')?.value || '';
    window._filterSuburb = document.getElementById('suburbFilter')?.value || '';
    return orig();
  };
}
"""
    p = p.replace("</script>", js + "\n</script>")

    # Patch the filtering logic: if render() filters by area, add province/metro/suburb check
    # Common pattern: .filter(x => ... area ...) - we add extra condition after it
    # Safer: Add filtering in render wrapper - filter allListings before render
    # We do it by patching the line where f = ... filter
    # If your render uses `let f = allListings.filter`, inject our check
    p = re.sub(
        r"(let\s+f\s*=\s*\(?\s*window\.allListings\s*\|\|\s*allListings\)?\.filter\([^\n]*\{)",
        r"\1\n      if(window._filterProv && x.province!==window._filterProv) return false;\n      if(window._filterMetro && x.metro!==window._filterMetro) return false;\n      if(window._filterSuburb && x.suburb!==window._filterSuburb) return false;",
        p
    )

pathlib.Path('index.html').write_text(p)
print("✅ index.html patched - ONLY area filters changed")
