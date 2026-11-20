import pathlib
p = pathlib.Path("index.html")
t = p.read_text()
# 1. Replace hardcoded cats + static dropdown with dynamic
t = t.replace(
    "const cats=['mechanic','dealership','tyres','car wash','spare parts','car rental'];",
    "let cats=[];"
)
# 2. In load(), build cats from real data + build dropdown + pills
t = t.replace(
    "document.getElementById('total').textContent=ALL.length+' listings - 9 provinces';",
    "cats=[...new Set(ALL.map(x=>x.category))].sort(); document.getElementById('cat').innerHTML='<option value=\"\">All Services</option>'+cats.map(c=>'<option>'+c+'</option>').join(''); document.getElementById('total').textContent=ALL.length+' listings - '+cats.length+' categories - 9 provinces';"
)
# 3. Use REAL audit score from listings.json if it exists
t = t.replace(
    "function scoreFor(x){let s=35;if(x.phone)s+=20;if(x.website)s+=15;if(x.rating)s+=15;if(x.reviews>20)s+=10;if(x.address&&x.address.length>15)s+=5;return Math.min(98,Math.max(35,s))}",
    "function scoreFor(x){if(x.audit&&x.audit.score)return x.audit.score; if(x.revenue_hunter&&x.revenue_hunter.score)return x.revenue_hunter.score; let s=35;if(x.phone)s+=20;if(x.website)s+=15;if(x.rating)s+=15;return s}"
)
# 4. Hero + nav: speak to ALL businesses, cars first
t = t.replace("South Africa's Trusted <em>Car Services</em> Marketplace", "South Africa's Trusted <em>Local Business</em> Marketplace")
t = t.replace("Find, compare and book verified mechanics, dealerships, tyre fitment centres and car washes near you.", "Find, compare and book verified mechanics, dealerships, restaurants, hotels, health, education and local services near you. 2,693 businesses. 9 provinces.")
t = t.replace("<a href=\"#\">Find Services</a><a href=\"#\">Dealerships</a><a href=\"#\">Tyres</a><a href=\"#\">Car Wash</a>", "<a href=\"#\">Find Services</a><a href=\"#\">Cars</a><a href=\"#\">Food</a><a href=\"#\">Health</a>")
# 5. Show monthly loss from real data in card (money hook)
t = t.replace(
    "<div class=\"muted\">'+(x.category)+'</div>",
    "<div class=\"muted\">'+(x.category)+' - '+(x.audit&&x.audit.monthly_loss_estimate?'Losing ~R'+x.audit.monthly_loss_estimate+'/mo':'')+'</div>"
)
p.write_text(t)
print("patched OK")
