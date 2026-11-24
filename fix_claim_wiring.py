import glob, re
for f in glob.glob("*.html"):
    if f.startswith("index.html.OLD"): continue
    t=open(f,encoding="utf-8",errors="ignore").read()
    orig=t
    # 1. CARD button: exact string from line 67 - leave WhatsApp <a class="wa"> alone
    t=t.replace(
        """<a class="claim" href="'+waLink(x)+'">Claim - R499/mo</a>""",
        """<a class="claim" href="javascript:void(0)" onclick="openClaim(ALL.indexOf(x))">Claim - FREE Audit</a>"""
    )
    # 2. MODAL buttons broken by previous regex - restore them
    t=t.replace(
        """<button class="btn btn-green" onclick="openClaim(ALL.indexOf(x))">✅ CLAIM + Send Audit on WhatsApp</button>""",
        """<button class="btn btn-green" onclick="submitClaim()">✅ CLAIM + Send Audit on WhatsApp</button>"""
    )
    t=t.replace(
        """<button class="btn btn-dark" onclick="openClaim(ALL.indexOf(x))">💳 PAY NOW - Secure Card via SimplyBlu</button>""",
        """<button class="btn btn-dark" onclick="payNowClaim()">💳 PAY NOW - Secure Card via SimplyBlu</button>"""
    )
    # 3. Checked logic: use real has_* flags, not always true
    t=t.replace(
        "{id:'photos',label:'📸 Professional Photos + Google Photos',price:799,checked:true}",
        "{id:'photos',label:'📸 Professional Photos + Google Photos',price:799,checked:!au.has_photos}"
    )
    t=t.replace(
        "{id:'whatsapp',label:'💬 WhatsApp Business Setup + Button',price:499,checked:true}",
        "{id:'whatsapp',label:'💬 WhatsApp Business Setup + Button',price:499,checked:!au.has_whatsapp}"
    )
    t=t.replace(
        "{id:'google',label:'📍 Google Business Profile Fix',price:699,checked:true}",
        "{id:'google',label:'📍 Google Business Profile Fix',price:699,checked:!au.has_rating}"
    )
    t=t.replace(
        "{id:'hours',label:'🕐 Opening Hours + Booking System',price:499,checked:true}",
        "{id:'hours',label:'🕐 Opening Hours + Booking System',price:499,checked:!au.has_hours}"
    )
    # 4. CSS for modal buttons - add if missing
    if ".btn-green{" not in t:
        css=".btn{display:block;text-align:center;text-decoration:none;padding:11px;border-radius:10px;font-weight:700;margin-top:8px;cursor:pointer;border:none;width:100%;font-size:15px}.btn-green{background:#25D366;color:#fff}.btn-dark{background:#111;color:#fff}.modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:99;overflow:auto}.modal-content{background:#fff;max-width:520px;margin:30px auto;padding:24px;border-radius:16px;color:#111}"
        t=t.replace("</style>", css+"</style>") if "</style>" in t else t.replace("</head>", f"<style>{css}</style></head>")
    # 5. Fix double-WhatsApp: sendToWhatomate should NOT open WhatsApp, payNowClaim already shows links
    t=t.replace(
        "  const msg = `🔥 UBernie CLAIM REQUEST\\n\\nBusiness: ${payload.business}",
        "  // no WhatsApp here - payNowClaim shows pay links, submitClaim handles WhatsApp\n  if(false){ const msg = `🔥 UBernie CLAIM REQUEST\\n\\nBusiness: ${payload.business}"
    )
    if t!=orig:
        open(f,"w",encoding="utf-8").write(t)
        print("fixed",f)
