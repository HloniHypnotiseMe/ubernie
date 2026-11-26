import pathlib, re
p = pathlib.Path("index.html")
t = p.read_text(encoding="utf-8")
# Find <section id="how-it-works"> ... </section>
m = re.search(r'(<section[^>]*id="how-it-works".*?</section>)', t, re.DOTALL)
if not m:
    print("NOT FOUND as section")
else:
    block = m.group(1)
    print(f"Found: {len(block)} chars at line {t[:m.start()].count(chr(10))+1}")
    t = t.replace(block, "", 1)
    # Insert BEFORE All Businesses button row (line 82)
    marker = 'All Businesses (2,693)'
    if marker in t:
        # Insert before the <div> that contains that button row
        # Find the div start before marker
        idx = t.find(marker)
        div_start = t.rfind('<div style="padding:10px 5%', 0, idx)
        if div_start != -1:
            t = t[:div_start] + block + "\n" + t[div_start:]
            print("Moved How It Works to BEFORE listings")
        else:
            t = t.replace(marker, block + marker, 1)
            print("Moved How It Works (fallback)")
    p.write_text(t, encoding="utf-8")
    print("DONE")
