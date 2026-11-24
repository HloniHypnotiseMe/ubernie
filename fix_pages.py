import pathlib, glob
for f in glob.glob("*.html"):
    t = pathlib.Path(f).read_text()
    # If FORCE_CAT exists, auto-set dropdown + render filter
    if "FORCE_CAT" in t and "if(window.FORCE_CAT)" not in t:
        t = t.replace("function render(){", "function render(){ if(window.FORCE_CAT){ var sel=document.getElementById('cat'); if(sel) sel.value=window.FORCE_CAT; cat=window.FORCE_CAT; }")
        pathlib.Path(f).write_text(t)
print("filter wired")
