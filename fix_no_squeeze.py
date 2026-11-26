import pathlib
p = pathlib.Path("category.html")
t = p.read_text(encoding="utf-8")

# 1. Content should NEVER have margin-left:230px - always full width
t = t.replace('style="margin-left:230px"', 'style="margin-left:0"')

# 2. Add overlay CSS - sidebar floats over content, content never moves
css = """
<style>
/* NO-SQUEEZE: sidebar is overlay, content always full width */
#sidebar{position:fixed!important;left:0;top:60px;bottom:0;width:260px;max-width:85vw;background:#f8f9fa!important;border-right:1px solid #ddd;padding:14px;z-index:100;overflow-y:auto;box-shadow:0 0 30px rgba(0,0,0,.25)}
#sidebar.closed{display:none!important}
div[style*="margin-left:"]{margin-left:0!important}
body.sidebar-closed div[style*="margin-left:"]{margin-left:0!important}
#sidebarOverlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:90}
#sidebarOverlay.show{display:block}
</style>
</body>"""
if "NO-SQUEEZE" not in t:
    t = t.replace("</body>", css, 1)
    print("Added no-squeeze CSS")

p.write_text(t, encoding="utf-8")
print("DONE")
