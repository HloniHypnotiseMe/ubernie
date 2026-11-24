import pathlib, glob, re, json

# --- WHAT TO REMOVE - exact phrases only ---
REMOVE = [
    "Our moat. Real vouchers from real local businesses.",
    "Our moat.",
    "Real vouchers from real local businesses. Claim a voucher, show it in-store, save.",
    "Claim a voucher, show it in-store, save.",
    "Trojan",
    "trojan",
]
# Keep "CLAIM VOUCHER" button - we do NOT touch that

report = []
for fname in sorted(glob.glob("*.html")):
    p = pathlib.Path(fname)
    t = p.read_text()
    orig = t
    for phrase in REMOVE:
        if phrase.lower() in t.lower():
            # case-insensitive remove
            t = re.sub(re.escape(phrase), "", t, flags=re.I)
            report.append(f"{fname}: removed '{phrase}'")
    # Clean double spaces / empty <p> left behind
    t = re.sub(r'<p>\s*</p>', '', t)
    t = re.sub(r'  +', ' ', t)
    if t != orig:
        p.write_text(t)

# --- AUDIT - check every page for consistency, don't change ---
print("\n=== AUDIT ===")
for fname in sorted(glob.glob("*.html")):
    t = pathlib.Path(fname).read_text()
    issues = []
    if "Our moat" in t: issues.append("STILL HAS MOAT")
    if "trojan" in t.lower(): issues.append("STILL HAS TROJAN")
    if "CLAIM VOUCHER" not in t and fname == "deals.html": issues.append("MISSING CLAIM VOUCHER")
    if "deals.html" not in t and fname not in ["deals.html"]: issues.append("NO LINK TO DEALS")
    if "<title>" not in t or "Ubernie" not in t: issues.append("BAD TITLE")
    # Brand check per page
    checks = {
        "restaurant.html": "IDLA NATHI",
        "food.html": "IDLA NATHI",
        "beauty.html": "BUHLE",
        "fashion.html": "SDWADLO",
        "education.html": "SGELA",
        "automotive.html": "CAR-LA-HURRY",
        "mechanic.html": "CAR-LA-HURRY",
        "drinkingwell.html": "DRINKINGWELL",
        "liquor.html": "DRINKINGWELL",
        "funeral.html": "LAST REST",
        "deals.html": "DEALS CORNER",
    }
    if fname in checks and checks[fname] not in t:
        issues.append(f"MISSING BRAND {checks[fname]}")
    # Footer / nav check
    if "ubernie.co.za" not in t.lower() and "Ubernie" not in t: issues.append("NO BRAND")
    status = "OK" if not issues else "FIX: " + ", ".join(issues)
    print(f"{fname:25} {status}")
    if "moat" in t.lower(): print(f"  -> MOAT STILL IN {fname}")

print("\n=== REMOVED ===")
for r in report: print(r)
if not report: print("Nothing to remove - already clean")
print("\n=== CLAIM VOUCHER CHECK ===")
for fname in sorted(glob.glob("*.html")):
    t = pathlib.Path(fname).read_text()
    c = t.count("CLAIM VOUCHER")
    if c: print(f"{fname}: {c}x CLAIM VOUCHER - KEPT")
