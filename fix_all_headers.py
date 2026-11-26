import pathlib, re, glob
for f in glob.glob("*.html"):
    p = pathlib.Path(f)
    t = p.read_text(encoding="utf-8", errors="ignore")
    orig = t
    if 'http-equiv="refresh"' in t:
        print(f"{f}: SKIP redirect"); continue
    if '<nav id="mainNav">' not in t and "<nav>" in t:
        t = t.replace("<nav>", '<nav id="mainNav">', 1)
    if "How It Works" not in t and "<nav" in t:
        link = '<a href="index.html#how-it-works">How It Works</a><a href="faq.html">Q&A / FAQ</a>'
        if 'deals.html' in t:
            t = re.sub(r'(<a[^>]*href="deals\.html")', link + r'\1', t, count=1)
        else:
            t = t.replace("</nav>", link + "</nav>", 1)
    elif "How It Works" in t and "faq.html" not in t and "<nav" in t:
        t = t.replace("</nav>", '<a href="faq.html">Q&A / FAQ</a></nav>', 1)
    if t != orig:
        p.write_text(t, encoding="utf-8"); print(f"{f}: FIXED")
    else:
        print(f"{f}: OK")
