import json, pathlib, re, collections
base = pathlib.Path("index.html").read_text()
d = json.load(open("listings.json"))
cats = sorted(set(x.get("category","other") for x in d))
print("CATS:", cats)
def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
for cat in cats:
    items = [x for x in d if x.get("category")==cat]
    s = slug(cat)
    # Build page: copy index.html but inject category filter + SEO
    html = base
    # SEO title
    html = html.replace("<title>", f"<title>{cat.title()} in South Africa | Ubernie - {len(items)} Listings | ", 1) if "<title>" in html else f"<title>{cat.title()} | Ubernie</title>\n"+html
    # Hero text replace
    html = html.replace("Local Business", f"{cat.title()}")
    # Inject auto-filter: force MODE + category on load
    inject = f"<script>window.FORCE_CAT='{cat}'; window.FORCE_MODE='all';</script>\n"
    html = html.replace("</body>", inject+"</body>")
    # Add a category header bar
    header = f'<div style="padding:20px 5%;background:#00C853;color:#000"><h1 style="margin:0">{cat.title()} in South Africa - {len(items)} Businesses</h1><p style="margin:4px 0 0">Find, compare, claim. Audit scores, monthly loss, RemotePay claim R499/mo. <a href="index.html" style="color:#000;font-weight:800">← Back to All</a></p></div>'
    html = html.replace('<div class="bar">', header+'<div class="bar">', 1) if '<div class="bar">' in html else header+html
    pathlib.Path(f"{s}.html").write_text(html)
    print(f"made {s}.html - {len(items)} listings")
# Also make category index list
idx = "<h2>All Categories</h2><ul>" + "".join([f'<li><a href="{slug(c)}.html">{c.title()} - {len([x for x in d if x.get("category")==c])}</a></li>' for c in cats]) + "</ul>"
pathlib.Path("categories.html").write_text(f"<html><body style='font-family:sans-serif;padding:20px'><h1>Ubernie Categories</h1>{idx}<p><a href='index.html'>Home</a></p></body></html>")
print("DONE - pages:", len(cats))
