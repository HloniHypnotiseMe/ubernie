import pathlib
p = pathlib.Path("audit_scorecard.py")
t = p.read_text()
print("BEFORE has car-rental?", "car-rental" in t)
# Add missing 4 to BRAND map
t = t.replace(
    '"dealership.html":"CAR-LA-HURRY"',
    '"dealership.html":"CAR-LA-HURRY","car-rental.html":"CAR-LA-HURRY","car-repair.html":"CAR-LA-HURRY","spare-parts.html":"CAR-LA-HURRY","day-care.html":"SGELA"'
)
# Fix H1 check: check ALL H1s, not just first
if 'hs=re.findall' not in t:
    t = t.replace(
        'h=re.search(r\'<h1[^>]*>(.*?)</h1>\', t, re.I|re.S)',
        'hs=re.findall(r\'<h1[^>]*>(.*?)</h1>\', t, re.I|re.S)'
    )
    t = t.replace(
        'checks["2_H1_Brand"] = 1 if (h and BRAND.get(fname,"UBERNIE") in re.sub(r\'<[^>]+>\',\'\',h.group(1)).upper()) else 0',
        'checks["2_H1_Brand"] = 1 if any(BRAND.get(fname,"UBERNIE") in re.sub(r\'<[^>]+>\',\'\',x).upper() for x in hs) else 0'
    )
p.write_text(t)
print("AFTER has car-rental?", "car-rental" in t)
print("map fixed")
