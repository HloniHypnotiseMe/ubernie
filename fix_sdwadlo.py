import pathlib, re
# Fashion is only 10 listings, but brand it properly
for fname in ["fashion.html"]:
    if pathlib.Path(fname).exists():
        t = pathlib.Path(fname).read_text()
        t = re.sub(r'<title>.*?</title>', '<title>Ubernie Sdwadlo | Clothing & Fashion South Africa</title>', t, count=1)
        # Replace hero heading with Sdwadlo
        if "SDWADLO" not in t:
            t = re.sub(r'<h1[^>]*>.*?</h1>', '<h1>UBERNIE <em>SDWADLO</em></h1>', t, count=1, flags=re.I)
            # Fallback if no h1 pattern matched
            if "SDWADLO" not in t:
                t = t.replace("South Africa's Trusted", "UBERNIE SDWADLO - South Africa's Trusted")
        # Add Sdwadlo intro + Deals teaser
        if "Sdwadlo" not in t or t.count("Sdwadlo") < 2:
            intro = '<div style="padding:18px 5%;background:#111;color:#fff;margin:16px 5%;border-radius:12px"><b>SDWADLO</b> - Clothing & Fashion. Local boutiques, streetwear, tailors & designers near you. <a href="deals.html" style="color:#FFD600;font-weight:800">View Fashion Deals in Deals Corner →</a></div>'
            t = t.replace('<div class="bar"><h2>Popular', intro + '<div class="bar"><h2>Popular', 1) if '<div class="bar"><h2>Popular' in t else intro + t
        pathlib.Path(fname).write_text(t)
        print(f"Sdwadlo -> {fname}")

# Update categories + index nav teaser to include Sdwadlo
for f in ["categories.html","index.html"]:
    if pathlib.Path(f).exists():
        txt = pathlib.Path(f).read_text()
        txt = txt.replace("Fashion -", "Sdwadlo - Fashion -")
        txt = txt.replace("fashion.html\">Fashion", "fashion.html\">Sdwadlo - Fashion")
        pathlib.Path(f).write_text(txt)
        print(f"updated {f}")
