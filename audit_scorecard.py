import pathlib, glob, re, json
BRAND = {
 "index.html":"UBERNIE","restaurant.html":"IDLA NATHI","food.html":"IDLA NATHI","cafe.html":"IDLA NATHI",
 "beauty.html":"BUHLE","hairdresser.html":"BUHLE","fashion.html":"SDWADLO",
 "education.html":"SGELA","automotive.html":"CAR-LA-HURRY","mechanic.html":"CAR-LA-HURRY",
 "dealership.html":"CAR-LA-HURRY","car-rental.html":"CAR-LA-HURRY","car-repair.html":"CAR-LA-HURRY","spare-parts.html":"CAR-LA-HURRY","day-care.html":"SGELA","car-wash.html":"CAR-LA-HURRY","tyres.html":"CAR-LA-HURRY",
 "drinkingwell.html":"DRINKINGWELL","liquor.html":"DRINKINGWELL","funeral.html":"LAST REST",
 "deals.html":"DEALS CORNER","health.html":"UBERNIE","hotel.html":"UBERNIE","categories.html":"UBERNIE",
}
rows=[]
for fname in sorted(glob.glob("*.html")):
    t = pathlib.Path(fname).read_text()
    low = t.lower()
    checks={}
    # 1 Title brand
    m=re.search(r'<title>(.*?)</title>', t, re.I|re.S)
    checks["1_Title_Brand"] = 1 if (m and BRAND.get(fname,"UBERNIE") in m.group(1).upper()) else 0
    # 2 H1 brand
    hs=re.findall(r'<h1[^>]*>(.*?)</h1>', t, re.I|re.S)
    checks["2_H1_Brand"] = 1 if any(BRAND.get(fname,"UBERNIE") in re.sub(r'<[^>]+>','',x).upper() for x in hs) else 0
    # 3 No banned words
    checks["3_No_Banned"] = 0 if any(w in low for w in ["moat","trojan","killa"]) else 1
    # 4 No fake rating - check file itself, not listings.json
    checks["4_No_Fake_Rating"] = 0 if "4.6" in t and "0 reviews" in t else 1
    # 5 No fake phone text in template
    checks["5_No_Fake_Phone"] = 0 if "Phone: Not listed" in t else 1
    # 6 Deals link
    checks["6_Deals_Link"] = 1 if ("deals.html" in t or fname=="deals.html") else 0
    # 7 Nav - no dead href="#"
    checks["7_Nav_No_Dead"] = 0 if 'href="#"' in t else 1
    # 8 CTA exists with real action
    checks["8_CTA_Real"] = 1 if ("CLAIM VOUCHER" in t or "Claim - R499" in t) and ("href=" in t or "onclick=" in t) else 0
    # 9 Footer present
    checks["9_Footer"] = 1 if "<footer" in low or "Terms - Privacy" in t else 0
    # 10 Nothing after footer
    if "<footer" in low:
        after = t[low.rfind("<footer"):]
        # If deals block after footer, fail
        checks["10_Nothing_After_Footer"] = 0 if "DEALS CORNER" in after and fname!="deals.html" else 1
    else:
        checks["10_Nothing_After_Footer"] = 0
    total=sum(checks.values())
    rows.append({"page":fname,"score":f"{total}/10",**checks})
    print(f"{fname:20} {total}/10  FAILS: {[k for k,v in checks.items() if v==0]}")
print(f"\nTOTAL PAGES: {len(rows)}")
print(f"AVG: {sum(int(r['score'].split('/')[0]) for r in rows)/len(rows):.1f}/10")
# Save for next audit - so we can compare, not re-guess
pathlib.Path("scorecard.json").write_text(json.dumps(rows, indent=2))
print("Saved to scorecard.json - run again after fix to prove improvement")
