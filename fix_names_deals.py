import pathlib, re, glob
# 1. Remove TROJAN word from ALL html if it ever slipped in
for f in glob.glob("*.html"):
    t = pathlib.Path(f).read_text()
    if "trojan" in t.lower():
        t = re.sub(r'trojan', '', t, flags=re.I)
        pathlib.Path(f).write_text(t)
        print(f"removed trojan from {f}")

base = pathlib.Path("index.html").read_text()

# 2. DEALS CORNER - OWN PAGE deals.html
deals_page = base
deals_page = re.sub(r'<title>.*?</title>', '<title>Ubernie Deals Corner | Vouchers & Discounts South Africa</title>', deals_page, count=1)
deals_page = deals_page.replace("Find <em>Idla Nathi</em>, <em>Buhle</em>, <em>DrinkingWell</em> & More Near You", "UBERNIE <em>DEALS CORNER</em>")
# Extract deals block if still in index, else build fresh
deals_block = '''
<div style="padding:28px 5%;background:#FFD600;color:#000;margin:20px 5%;border-radius:12px">
<h2>🔥 DEALS CORNER - VOUCHERS & DISCOUNTS</h2>
<p>Real vouchers from real local businesses. Claim, show in-store, save.</p>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-top:14px">
<div style="background:#fff;padding:16px;border-radius:10px"><b>20% OFF First Visit</b><br><small>Buhle - Beauty Salons</small><br><button onclick="alert('Voucher saved! Code: BUHLE20')" style="margin-top:8px;padding:10px 14px;background:#000;color:#fff;border:0;border-radius:6px;font-weight:700">CLAIM VOUCHER</button></div>
<div style="background:#fff;padding:16px;border-radius:10px"><b>R50 OFF Meal</b><br><small>Idla Nathi - Restaurants</small><br><button onclick="alert('Voucher saved! Code: IDLA50')" style="margin-top:8px;padding:10px 14px;background:#000;color:#fff;border:0;border-radius:6px;font-weight:700">CLAIM VOUCHER</button></div>
<div style="background:#fff;padding:16px;border-radius:10px"><b>Free Safety Check</b><br><small>Car-La-Hurry - Mechanics</small><br><button onclick="alert('Voucher saved! Code: SAFETYFREE')" style="margin-top:8px;padding:10px 14px;background:#000;color:#fff;border:0;border-radius:6px;font-weight:700">CLAIM VOUCHER</button></div>
<div style="background:#fff;padding:16px;border-radius:10px"><b>SmartDrinker Ride - R30 OFF</b><br><small>DrinkingWell - Take Me Home</small><br><button onclick="alert('Voucher saved! Code: HOME30')" style="margin-top:8px;padding:10px 14px;background:#000;color:#fff;border:0;border-radius:6px;font-weight:700">JOIN + CLAIM</button></div>
</div>
<p style="font-size:13px;margin-top:12px">Businesses: Add your voucher to Deals Corner when you claim - R499/mo via RemotePay.</p>
</div>
'''
# Put deals block right after hero in deals.html, remove listings grid confusion - keep it simple: deals + grid
deals_page = deals_page.replace('<div class="bar"><h2>Popular', deals_block + '<div class="bar"><h2>Popular', 1)
pathlib.Path("deals.html").write_text(deals_page)
print("made deals.html")

# 3. Fix INDEX - replace full Deals block with small teaser linking to deals.html
idx = pathlib.Path("index.html").read_text()
# Remove large deals block from index, replace with teaser
idx = re.sub(r'<div style="padding:28px 5%;background:#FFD600.*?(?=<div class="bar"><h2>Popular|<div style="padding:14px 5%;background:#111)', '', idx, count=1, flags=re.S)
teaser = '<div style="padding:18px 5%;background:#FFD600;color:#000;margin:16px 5%;border-radius:12px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:center"><span><b>🔥 DEALS CORNER</b> - Vouchers & Discounts. Claim & save.</span><a href="deals.html" style="background:#000;color:#fff;padding:10px 16px;border-radius:8px;font-weight:800">View All Deals →</a></div>'
if "deals.html" not in idx:
    idx = idx.replace('<div class="bar"><h2>Popular', teaser + '<div class="bar"><h2>Popular', 1)
# Add Deals to nav
idx = idx.replace('For Business</a>', 'For Business</a><a href="deals.html" style="color:#FFD600;font-weight:800">Deals Corner</a>')
pathlib.Path("index.html").write_text(idx)
print("index now teasers to deals.html")

# 4. CAR-LA-HURRY - automotives / cars
for fname in ["automotive.html","mechanic.html","dealership.html","car-repair.html","car-wash.html","car-rental.html","tyres.html","spare-parts.html"]:
    if pathlib.Path(fname).exists():
        txt = pathlib.Path(fname).read_text()
        txt = re.sub(r'<title>.*?</title>', '<title>Ubernie Car-La-Hurry | Cars & Automotive South Africa</title>', txt, count=1)
        # Replace hero heading if generic
        txt = re.sub(r'Find.*Near You|South Africa.*Marketplace|UBERNIE.*', 'UBERNIE <em>CAR-LA-HURRY</em>', txt, count=1) if "CAR-LA-HURRY" not in txt else txt
        # Ensure heading contains Car-La-Hurry
        if "CAR-LA-HURRY" not in txt:
            txt = txt.replace('<h1>', '<h1>UBERNIE CAR-LA-HURRY - ', 1)
        pathlib.Path(fname).write_text(txt)
        print(f"Car-La-Hurry -> {fname}")

# 5. IDLA NATHI + BUHLE - enforce on their pages
for fname, title in [("restaurant.html","Ubernie Idla Nathi | Restaurants"), ("food.html","Ubernie Idla Nathi | Food"), ("cafe.html","Ubernie Idla Nathi | Cafes"), ("beauty.html","Ubernie Buhle | Beauty"), ("hairdresser.html","Ubernie Buhle | Hair")]:
    if pathlib.Path(fname).exists():
        txt = pathlib.Path(fname).read_text()
        txt = re.sub(r'<title>.*?</title>', f'<title>{title} South Africa</title>', txt, count=1)
        pathlib.Path(fname).write_text(txt)
        print(f"renamed {fname} -> {title}")

# 6. Categories page - show brand names
if pathlib.Path("categories.html").exists():
    c = pathlib.Path("categories.html").read_text()
    c = c.replace("Restaurant -", "Idla Nathi - Restaurant -")
    c = c.replace("Beauty -", "Buhle - Beauty -")
    c = c.replace("Automotive -", "Car-La-Hurry - Automotive -")
    c = c.replace("Mechanic -", "Car-La-Hurry - Mechanic -")
    c += '<p><a href="deals.html" style="font-weight:800;color:#000;background:#FFD600;padding:8px 14px;border-radius:8px">🔥 Deals Corner - Vouchers & Discounts</a> | <a href="drinkingwell.html">DrinkingWell</a> | <a href="funeral.html">Last Rest</a></p>'
    pathlib.Path("categories.html").write_text(c)
    print("categories updated")
