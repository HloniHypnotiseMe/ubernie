import pathlib, glob, re
for f in glob.glob("*.html"):
    t = pathlib.Path(f).read_text()
    orig = t
    # 1. REMOVE Goodfellas Killa copy everywhere - all variants
    t = t.replace("Goodfellas Killa", "Take Me Home service")
    t = t.replace("Goodfellas Killa.", "Take Me Home service.")
    t = t.replace("Goodfellas Killa -", "Take Me Home -")
    t = t.replace("GOODFELLAS KILLA", "TAKE ME HOME")
    t = re.sub(r'Goodfellas.*?Killa', 'Take Me Home service', t, flags=re.I)
    t = re.sub(r'Goodfellas Killa', '', t, flags=re.I)
    # 2. Fix SmartDrinker description to correct one
    t = t.replace("Know before you go - which spots are open", "Book a safe ride home after your night out - like Goodfellas, built for DrinkingWell")
    t = t.replace("which spots are open, what&apos;s on, how to get home safe.", "Book a safe ride home after your night out.")
    t = t.replace("Know before you go", "Book a safe ride home")
    # 3. Add DEALS CORNER if not there - our moat
    if "DEALS CORNER" not in t and f in ["index.html","drinkingwell.html","restaurant.html","beauty.html","funeral.html","liquor.html"]:
        deals = '''
<div style="padding:28px 5%;background:#FFD600;color:#000;margin:20px 5%;border-radius:12px">
<h2 style="margin:0">🔥 UBERNIE DEALS CORNER - VOUCHERS & DISCOUNTS</h2>
<p style="margin:8px 0">Our moat. Real vouchers from real local businesses. Claim a voucher, show it in-store, save.</p>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:12px">
<div style="background:#fff;padding:14px;border-radius:10px"><b>20% OFF First Visit</b><br><small>Beauty - Buhle Salons</small><br><button onclick="alert('Voucher saved! Show this at the salon. Code: BUHLE20')" style="margin-top:8px;padding:8px 12px;background:#000;color:#fff;border:0;border-radius:6px;font-weight:700">CLAIM VOUCHER</button></div>
<div style="background:#fff;padding:14px;border-radius:10px"><b>R50 OFF Meal</b><br><small>Restaurants - Idla Nathi</small><br><button onclick="alert('Voucher saved! Code: IDLA50')" style="margin-top:8px;padding:8px 12px;background:#000;color:#fff;border:0;border-radius:6px;font-weight:700">CLAIM VOUCHER</button></div>
<div style="background:#fff;padding:14px;border-radius:10px"><b>Free Safety Check</b><br><small>Mechanics</small><br><button onclick="alert('Voucher saved! Code: SAFETYFREE')" style="margin-top:8px;padding:8px 12px;background:#000;color:#fff;border:0;border-radius:6px;font-weight:700">CLAIM VOUCHER</button></div>
<div style="background:#fff;padding:14px;border-radius:10px"><b>SmartDrinker Ride - R30 OFF</b><br><small>DrinkingWell - Take Me Home</small><br><button onclick="alert('You are on SmartDrinker list. Ride voucher: HOME30')" style="margin-top:8px;padding:8px 12px;background:#000;color:#fff;border:0;border-radius:6px;font-weight:700">JOIN + CLAIM</button></div>
</div>
<p style="font-size:12px;margin-top:10px">Businesses: Add your voucher to Deals Corner when you claim - R499/mo via RemotePay. Vouchers bring customers, not just listings.</p>
</div>
'''
        # Insert before footer or before </body>
        if "</footer>" in t:
            t = t.replace("</footer>", deals + "</footer>")
        else:
            t = t.replace("</body>", deals + "</body>")
    if t != orig:
        pathlib.Path(f).write_text(t)
        print(f"fixed {f}")
print("DONE - check no Goodfellas Killa left:")
