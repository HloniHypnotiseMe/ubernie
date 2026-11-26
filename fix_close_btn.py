import pathlib, re
p = pathlib.Path("category.html")
t = p.read_text(encoding="utf-8")

# 1. Replace toggleSidebar with a robust version that uses BOTH .open AND .closed + inline style
old_pat = re.compile(r"function toggleSidebar\(force\)\{.*?^\}", re.MULTILINE|re.DOTALL)
new_fn = """function toggleSidebar(force){
  var s=document.getElementById('sidebar'); var o=document.getElementById('sidebarOverlay'); var b=document.getElementById('menuBtn');
  if(!s) return;
  var willOpen = (force!==undefined)? force : !s.classList.contains('open');
  s.classList.toggle('open', willOpen);
  s.classList.toggle('closed', !willOpen);
  s.style.display = willOpen ? 'block' : 'none';
  if(o) o.classList.toggle('show', willOpen);
  document.body.classList.toggle('sidebar-closed', !willOpen);
  if(b) b.textContent = willOpen ? '✕ Close' : '☰ Categories';
  return false;
}"""
t2, n = old_pat.subn(new_fn, t, count=1)
print(f"toggleSidebar replaced: {n}")
t = t2

# 2. Remove the JS that creates a second Close button inside sidebar - we will use a static one
t = t.replace("""  if(!document.getElementById('sidebarClose')){
    var c=document.createElement('button'); c.id='sidebarClose'; c.textContent='✕ Close'; c.onclick=function(){toggleSidebar(false)}; s.prepend(c);
  }""", "")

# 3. Add a STATIC Close button as first child of sidebar, if not already there
if '<button id="sidebarClose"' not in t:
    t = t.replace('<aside id="sidebar" class="open">', '<aside id="sidebar" class="open"><button id="sidebarClose" onclick="toggleSidebar(false);return false;" style="display:block;text-align:right;font-size:22px;cursor:pointer;background:none;border:0;width:100%;color:#111">✕ Close</button>', 1)
    print("Added static Close button")

# 4. Add bulletproof CSS - closed ALWAYS hides, on desktop AND mobile
css = """
<style>
/* CLOSE BUTTON FIX - closed always hides */
#sidebar.closed{display:none!important}
#sidebarClose{display:block!important;cursor:pointer}
body.sidebar-closed div[style*="margin-left:230px"]{margin-left:0!important}
</style>
</body>"""
if "CLOSE BUTTON FIX" not in t:
    t = t.replace("</body>", css, 1)
    print("Added close-fix CSS")

p.write_text(t, encoding="utf-8")
print("DONE - toggleSidebar defs:", t.count("function toggleSidebar"))
