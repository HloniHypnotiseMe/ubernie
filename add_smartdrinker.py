import pathlib, glob
# Change this if filename is different
target = "drinkingwell.html"
# If file doesn't exist, copy restaurant.html as base
if not pathlib.Path(target).exists():
    src = pathlib.Path("restaurant.html").read_text() if pathlib.Path("restaurant.html").exists() else pathlib.Path("index.html").read_text()
    pathlib.Path(target).write_text(src)
    print(f"created {target} from base")

t = pathlib.Path(target).read_text()
t = re.sub(r'<title>.*?</title>', '<title>Ubernie DrinkingWell | Bars & Drinking Places | SmartDrinker Waiting List</title>', t, count=1) if False else t
import re
t = re.sub(r'<title>.*?</title>', '<title>Ubernie DrinkingWell | Bars & Drinking Places | SmartDrinker Waiting List</title>', t, count=1, flags=re.I)
t = re.sub(r'<h1[^>]*>.*?</h1>', '<h1>UBERNIE DRINKINGWELL</h1>', t, count=1, flags=re.I)

smart = '''
<div style="padding:28px 5%;background:#111;color:#fff;border:3px solid #FFD600;margin:20px 5%;border-radius:12px">
<h2 style="margin:0;color:#FFD600">SMARTDRINKER - JOIN THE WAITING LIST</h2>
<p style="font-size:16px">Goodfellas Killa. Know before you go - which spots are open, what&apos;s on, how to get home safe. No more runaround.</p>
<form onsubmit="event.preventDefault(); localStorage.setItem('smartdrinker_'+this.phone.value, this.name.value); alert('You are on the SmartDrinker waiting list. We will contact you.'); this.reset();" style="display:flex;gap:10px;flex-wrap:wrap">
<input name="name" placeholder="Your Name" required style="padding:12px;flex:1;min-width:160px;border-radius:8px;border:0">
<input name="phone" placeholder="WhatsApp Number" required style="padding:12px;flex:1;min-width:160px;border-radius:8px;border:0">
<input name="area" placeholder="Area - e.g Soweto, Sandton" style="padding:12px;flex:1;min-width:160px;border-radius:8px;border:0">
<button style="padding:12px 22px;background:#FFD600;color:#000;font-weight:800;border:0;border-radius:8px;cursor:pointer">JOIN WAITING LIST</button>
</form>
<p style="font-size:12px;opacity:.7">Bars: claim your DrinkingWell page to be listed on SmartDrinker first. R499/mo via RemotePay.</p>
</div>
'''
if "SMARTDRINKER" not in t:
    t = t.replace('<div class="bar">', smart+'<div class="bar">', 1) if '<div class="bar">' in t else smart+t
    pathlib.Path(target).write_text(t)
    print(f"SMARTDRINKER added to {target}")
else:
    print("already there")
