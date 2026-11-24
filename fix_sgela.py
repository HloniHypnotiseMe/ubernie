import pathlib, re
for fname in ["education.html"]:
    if pathlib.Path(fname).exists():
        t = pathlib.Path(fname).read_text()
        t = re.sub(r'<title>.*?</title>', '<title>Ubernie Sgela | Education South Africa</title>', t, count=1)
        if "SGELA" not in t:
            t = re.sub(r'<h1[^>]*>.*?</h1>', '<h1>UBERNIE <em>SGELA</em></h1>', t, count=1, flags=re.I)
            if "SGELA" not in t:
                t = t.replace("South Africa's Trusted", "UBERNIE SGELA - South Africa's Trusted")
        if t.count("Sgela") < 2:
            intro = '<div style="padding:18px 5%;background:#111;color:#fff;margin:16px 5%;border-radius:12px"><b>SGELA</b> - Education. Schools, day-care, tutoring, colleges & training near you. <a href="deals.html" style="color:#FFD600;font-weight:800">View Education Deals in Deals Corner →</a></div>'
            t = t.replace('<div class="bar"><h2>Popular', intro + '<div class="bar"><h2>Popular', 1) if '<div class="bar"><h2>Popular' in t else intro + t
        pathlib.Path(fname).write_text(t)
        print(f"Sgela -> {fname}")

for f in ["categories.html","index.html"]:
    if pathlib.Path(f).exists():
        txt = pathlib.Path(f).read_text()
        txt = txt.replace("Education -", "Sgela - Education -")
        txt = txt.replace('education.html">Education', 'education.html">Sgela - Education')
        pathlib.Path(f).write_text(txt)
        print(f"updated {f}")
