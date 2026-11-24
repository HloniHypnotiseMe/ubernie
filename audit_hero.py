import pathlib, glob, re, collections
heroes = {}
for fname in sorted(glob.glob("*.html")):
    t = pathlib.Path(fname).read_text()
    # Grab hero <p> after first <h1>
    m = re.search(r'<h1[^>]*>.*?</h1>\s*<p>(.*?)</p>', t, re.I|re.S)
    if m:
        txt = re.sub(r'<[^>]+>', '', m.group(1)).strip()[:120]
        heroes[fname] = txt
    else:
        heroes[fname] = "NO HERO P FOUND"
# Count duplicates
c = collections.Counter(heroes.values())
for txt, count in c.most_common():
    print(f"{count}x : {txt}")
    if count > 1:
        for f, v in heroes.items():
            if v == txt:
                print(f"  - {f}")
