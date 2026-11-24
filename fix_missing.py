import pathlib, re
base = pathlib.Path("index.html").read_text()

def make_page(fname, title, h1, cat_filter, extra_html):
    html = base
    html = re.sub(r'<title>.*?</title>', f'<title>{title} | Ubernie</title>', html, count=1)
    html = html.replace("South Africa's Trusted <em>Local Business</em> Marketplace", h1)
    # Force filter to this category
    inject = f"<script>window.addEventListener('load',()=>{{let s=document.getElementById('cat'); if(s){{s.value='{cat_filter}'; s.dispatchEvent(new Event('change'));}}}});</script>"
    html = html.replace("</body>", extra_html + inject + "</body>")
    pathlib.Path(fname).write_text(html)
    print(f"made {fname} -> filter={cat_filter}")

# 1. DRINKINGWELL - from liquor (13 listings)
smart = '''
<div style="padding:28px 5%;background:#111;color:#fff;border:3px solid #FFD600;margin:20px 5%;border-radius:12px">
<h2 style="margin:0;color:#FFD600">SMARTDRINKER - JOIN THE WAITING LIST</h2>
<p>Goodfellas Killa. Know before you go - which spots are open, what&apos;s on, how to get home safe.</p>
<form onsubmit="event.preventDefault(); alert('You are on the SmartDrinker waiting list.'); this.reset();" style="display:flex;gap:10px;flex-wrap:wrap">
<input placeholder="Your Name" required style="padding:12px;flex:1;min-width:140px;border-radius:8px;border:0">
<input placeholder="WhatsApp Number" required style="padding:12px;flex:1;min-width:140px;border-radius:8px;border:0">
<input placeholder="Area - e.g Soweto, Sandton" style="padding:12px;flex:1;min-width:140px;border-radius:8px;border:0">
<button style="padding:12px 22px;background:#FFD600;color:#000;font-weight:800;border:0;border-radius:8px">JOIN WAITING LIST</button>
</form><p style="font-size:12px;opacity:.7">Bars: claim your DrinkingWell page to be on SmartDrinker first. R499/mo via RemotePay.</p></div>
'''
make_page("drinkingwell.html", "Ubernie DrinkingWell | Bars & Drinking Places | SmartDrinker Waiting List", "UBERNIE <em>DRINKINGWELL</em>", "liquor", smart)
# Also keep liquor.html as alias copy
pathlib.Path("liquor.html").write_text(pathlib.Path("drinkingwell.html").read_text())

# 2. LAST REST - 0 listings, so lead capture page
last_rest = '''
<div style="padding:28px 5%;background:#12210f;color:#fff;margin:20px 5%;border-radius:12px">
<h2>UBERNIE LAST REST - Funeral Services</h2>
<p>We are building the trusted list for funeral services across South Africa. No listings yet in your area - be first.</p>
<form onsubmit="event.preventDefault(); alert('Thank you. We will contact you about Last Rest.'); this.reset();" style="display:flex;gap:10px;flex-wrap:wrap">
<input placeholder="Your Name" required style="padding:12px;flex:1;border-radius:8px;border:0">
<input placeholder="WhatsApp" required style="padding:12px;flex:1;border-radius:8px;border:0">
<input placeholder="Area / Province" style="padding:12px;flex:1;border-radius:8px;border:0">
<button style="padding:12px 22px;background:#7ED321;color:#000;font-weight:800;border:0;border-radius:8px">REQUEST FUNERAL SERVICE / LIST MY BUSINESS</button>
</form></div>
'''
make_page("funeral.html", "Ubernie Last Rest | Funeral Services South Africa", "UBERNIE <em>LAST REST</em>", "", last_rest)

# 3. Fix the two titles you already gave me
for f, t, h in [("restaurant.html","Ubernie Idla Nathi | Restaurants South Africa","UBERNIE <em>IDLA NATHI</em>"), ("beauty.html","Ubernie Buhle | Beauty South Africa","UBERNIE <em>BUHLE</em>")]:
    txt = pathlib.Path(f).read_text()
    txt = re.sub(r'<title>.*?</title>', f'<title>{t}</title>', txt, count=1)
    txt = txt.replace("South Africa's Trusted <em>Local Business</em> Marketplace", h)
    pathlib.Path(f).write_text(txt)
    print(f"renamed {f} -> {t}")
