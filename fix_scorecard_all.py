import pathlib, glob, re
BRAND = {
 "index.html":"UBERNIE","restaurant.html":"IDLA NATHI","food.html":"IDLA NATHI","cafe.html":"IDLA NATHI",
 "beauty.html":"BUHLE","hairdresser.html":"BUHLE","fashion.html":"SDWADLO",
 "education.html":"SGELA","day-care.html":"SGELA",
 "automotive.html":"CAR-LA-HURRY","mechanic.html":"CAR-LA-HURRY","dealership.html":"CAR-LA-HURRY",
 "car-wash.html":"CAR-LA-HURRY","car-rental.html":"CAR-LA-HURRY","car-repair.html":"CAR-LA-HURRY",
 "tyres.html":"CAR-LA-HURRY","spare-parts.html":"CAR-LA-HURRY",
 "drinkingwell.html":"DRINKINGWELL","liquor.html":"DRINKINGWELL",
 "funeral.html":"LAST REST","deals.html":"DEALS CORNER",
 # Unnamed categories - keep UBERNIE + category name in H1, so they still pass
 "accommodation.html":"UBERNIE","airbnb.html":"UBERNIE","electronics.html":"UBERNIE","fitness.html":"UBERNIE",
 "grocery.html":"UBERNIE","health.html":"UBERNIE","hotel.html":"UBERNIE","pets.html":"UBERNIE",
 "pharmacy.html":"UBERNIE","property.html":"UBERNIE","services.html":"UBERNIE","supermarket.html":"UBERNIE",
 "categories.html":"UBERNIE",
}
for fname in sorted(glob.glob("*.html")):
    p = pathlib.Path(fname)
    t = p.read_text()
    orig = t
    brand = BRAND.get(fname, "UBERNIE")

    # FIX 5: Fake phone -> honest copy. Do NOT delete phone logic, just template text
    t = t.replace("Phone: Not listed - Claim to add", "Claim to add phone & verify")
    t = t.replace("Phone: Not listed", "Claim to add phone")

    # FIX 7: Dead nav -> real pages
    t = t.replace('href="#"', 'href="categories.html"')
    # Fix specific dead nav if still generic
    t = t.replace('<a href="categories.html">Find Services</a>', '<a href="categories.html">Find Services</a>')

    # FIX 6: Add Deals link to nav if missing - insert before </nav> or after first nav link
    if "deals.html" not in t and fname != "deals.html":
        # Try nav
        if "</nav>" in t:
            t = t.replace("</nav>", '<a href="deals.html" style="color:#FFD600;font-weight:800">Deals Corner</a></nav>', 1)
        elif '<header' in t:
            # Insert after header open
            t = re.sub(r'(<header[^>]*>)', r'\1<a href="deals.html" style="color:#FFD600;font-weight:800">Deals Corner</a>', t, count=1, flags=re.I)
        else:
            # Fallback: top of body
            t = t.replace("<body>", '<body><div style="text-align:center;padding:8px;background:#FFD600"><a href="deals.html" style="color:#000;font-weight:800">🔥 DEALS CORNER - View Vouchers →</a></div>', 1)

    # FIX 2: H1 brand - if H1 exists but no brand, prepend brand. If no H1, add one after header/body
    h = re.search(r'<h1[^>]*>(.*?)</h1>', t, re.I|re.S)
    if h:
        inner = re.sub(r'<[^>]+>', '', h.group(1))
        if brand not in inner.upper():
            # Keep original text, prepend brand
            new_h1 = h.group(0).replace(h.group(1), f"{brand} - {h.group(1)}")
            t = t.replace(h.group(0), new_h1, 1)
    else:
        # No H1 - add one right after <body> or <header>
        h1_tag = f'<h1 style="text-align:center;padding:20px 5% 0">UBERNIE {brand}</h1>'
        if "<body>" in t:
            t = t.replace("<body>", "<body>" + h1_tag, 1)
        else:
            t = h1_tag + t

    # FIX 10: Move content after footer before footer - simple: if DEALS after footer, move it before footer
    # We do this only if footer exists and deals block after it
    low = t.lower()
    if "<footer" in low and "deals corner" in low[low.rfind("<footer"):]:
        # Cut deals block after footer and re-insert before footer - safe: find deals div after footer
        footer_idx = low.rfind("<footer")
        after = t[footer_idx:]
        # Find deals div in after
        m = re.search(r'<div[^>]*>.*?DEALS CORNER.*?</div>\s*</div>', after, flags=re.I|re.S)
        if m:
            deals_block = m.group(0)
            t = t[:footer_idx] + deals_block + t[footer_idx:].replace(deals_block, "", 1)
            print(f"{fname}: moved deals before footer")

    if t != orig:
        p.write_text(t)
        print(f"fixed {fname}")
print("done")
