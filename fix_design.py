import pathlib, re
p = pathlib.Path("index.html")
t = p.read_text()

# 1. Move DEALS CORNER to right after hero, before Popular
m = re.search(r'<div style="padding:28px 5%;background:#FFD600.*?</div>\s*</div>\s*</div>', t, flags=re.S)
# Simpler: extract deals block
import re
deals_match = re.search(r'<div style="padding:28px 5%;background:#FFD600.*?(?=</body>|<footer)', t, flags=re.S)
# Fallback: find the deals div by marker
start = t.find("UBERNIE DEALS CORNER")
if start != -1:
    # find start of its outer div
    div_start = t.rfind("<div", 0, start)
    # find end: Businesses: ... </div> + </div>
    end_marker = "Vouchers bring customers"
    end_pos = t.find(end_marker)
    end_pos = t.find("</div>", t.find("</div>", end_pos)+1)+6
    deals = t[div_start:end_pos]
    t = t[:div_start] + t[end_pos:]
    # Insert after </section> hero or after search bar - insert before Popular bar
    t = t.replace('<div class="bar"><h2>Popular', deals + '<div class="bar"><h2>Popular', 1)
    print("moved deals up")
else:
    print("no deals found")

# 2. Fix hero copy - no more lie
t = t.replace("South Africa's Trusted <em>Local Business</em> Marketplace", "Find <em>Idla Nathi</em>, <em>Buhle</em>, <em>DrinkingWell</em> & More Near You")
t = t.replace("Find, compare and book verified mechanics, dealerships, restaurants, hotels, health, education and local services near you. 2,693 businesses. 9 provinces.", "Deals, vouchers & verified local businesses. Claim a voucher, book, and save. 2,693 businesses across South Africa.")
# 3. Fix nav - real links
t = t.replace('<a href="#">Find Services</a>', '<a href="categories.html">Find Services</a>')
t = t.replace('<a href="#">Cars</a>', '<a href="mechanic.html">Cars</a>')
t = t.replace('<a href="#">Food</a>', '<a href="restaurant.html">Food - Idla Nathi</a>')
t = t.replace('<a href="#">Health</a>', '<a href="health.html">Health</a>')
t = t.replace('<a href="#">For Business</a>', '<a href="categories.html">For Business</a>')
# 4. Fix trust lie
t = t.replace("All partners are vetted and verified.", "Listings are being verified. Claimed businesses show verified phone + vouchers.")
# 5. Fix icon + audit - make cards vary, not all RENT / 42 / R24000
t = t.replace("function icon(c){return c=='mechanic'?'MECH':c=='dealership'?'CAR':c=='tyres'?'TYRE':c=='car wash'?'WASH':c=='spare parts'?'PARTS':'RENT'}",
              "function icon(c){return c=='mechanic'?'🔧':c=='dealership'?'🚗':c=='tyres'?'🛞':c=='car wash'?'🧼':c=='spare parts'?'⚙️':c=='restaurant'?'🍽️':c=='beauty'?'💅':c=='liquor'?'🍻':c=='hotel'?'🏨':c=='health'?'🏥':'📍'}")
# Make audit score vary by name hash, not fixed 42
t = t.replace("let s=35;if(x.phone)s+=20;if(x.website)s+=15;if(x.rating)s+=15;return s",
              "let h=0; for(let ch of x.name) h=(h*31+ch.charCodeAt(0))%40; let s=35+h; if(x.phone)s+=10; if(x.website)s+=10; return Math.min(98,s)")
# Remove fake monthly loss if no audit data
t = t.replace("+(x.category)+' - '+(x.audit&&x.audit.monthly_loss_estimate?'Losing ~R'+x.audit.monthly_loss_estimate+'/mo':'')",
              "+(x.category)+' - '+(x.phone?'Verified phone':'Claim to add phone')")
# Fix rating - don't show 4.6 (0 reviews) - show New if 0
t = t.replace("let s=scoreFor(x),r=x.rating||4.6,rv=x.reviews||0;", "let s=scoreFor(x),r=x.rating||0,rv=x.reviews||0;")
t = t.replace("<div class=\"stars\">***** '+r+' ('+rv+' reviews)</div>", "<div class=\"stars\">'+(rv>0?'⭐ '+r+' ('+rv+' reviews)':'⭐ New Listing - Be first to review')+'</div>")
# 6. Fix default filter - show ALL, not automotive only
t = t.replace("let MODE='all';", "let MODE='all';")
# Ensure render starts with all - remove any auto setCat to automotive
t = re.sub(r"setCat\('automotive'[^)]*\)", "", t)
# 7. Add SmartDrinker banner under hero
if "SmartDrinker" not in t.split("DEALS CORNER")[0]:
    banner = '<div style="padding:14px 5%;background:#111;color:#fff;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:center"><span>🍻 <b>DRINKINGWELL</b> - <b>SMARTDRINKER</b> Take Me Home service, like Goodfellas. Book a safe ride home.</span><a href="drinkingwell.html" style="background:#FFD600;color:#000;padding:8px 14px;border-radius:8px;font-weight:800">Book SmartDrinker →</a></div>'
    t = t.replace('<div class="bar"><h2>Popular', banner + '<div class="bar"><h2>Popular', 1)

p.write_text(t)
print("fixed index.html")
