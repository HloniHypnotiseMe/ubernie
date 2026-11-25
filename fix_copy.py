import glob
replacements=[
    ("RemotePay claim R499/mo", "FREE Claim + Audit - fixes from R299"),
    ("Get Started - R499/mo", "Claim FREE - Audit + Fixes"),
    ("Businesses: Add your voucher to Deals Corner when you claim - R499/mo via RemotePay. Vouchers bring customers, not just listings.",
     "Businesses: Claim FREE - Add your voucher to Deals Corner. Vouchers bring customers, not just listings."),
    ("when you claim - R499/mo", "when you claim - FREE"),
    ("Claim - R499/mo", "Claim - FREE Audit"),
    ("List Your Business", "Claim Your Business - FREE"),
]
for f in glob.glob("*.html"):
    t=open(f,encoding="utf-8",errors="ignore").read()
    orig=t
    for a,b in replacements:
        t=t.replace(a,b)
    if t!=orig:
        open(f,"w",encoding="utf-8").write(t)
        print("copy fixed",f)
