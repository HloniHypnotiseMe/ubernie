import pathlib
p = pathlib.Path("index.html")
t = p.read_text()
# 1. Define car categories
old = "let cats=[];"
new = "let cats=[]; const CAR_CATS=['mechanic','dealership','spare parts','car repair','car rental','tyres','car wash','automotive']; let MODE='all';"
t = t.replace(old, new)
# 2. Add toggle UI before the bar
t = t.replace(
    '<div class="bar">',
    '<div style="padding:10px 5%;display:flex;gap:8px;flex-wrap:wrap"><button class="btn" id="btnAll" onclick="setMode(\'all\')">All Businesses (2,693)</button><button class="btn-outline" id="btnCars" onclick="setMode(\'cars\')">Cars Only (1,092)</button><button class="btn-outline" id="btnLocal" onclick="setMode(\'local\')">Food / Health / Local</button></div><div class="bar">'
)
# 3. Add setMode function + filter in render()
t = t.replace(
    "function setCat(c,el){",
    "function setMode(m){MODE=m; document.getElementById('btnAll').className=m=='all'?'btn':'btn-outline'; document.getElementById('btnCars').className=m=='cars'?'btn':'btn-outline'; document.getElementById('btnLocal').className=m=='local'?'btn':'btn-outline'; render()} function setCat(c,el){"
)
# 4. Make render() respect MODE
t = t.replace(
    "let f=ALL.filter(x=>(!cat||x.category==cat)",
    "let f=ALL.filter(x=>((MODE=='all')||(MODE=='cars'&&CAR_CATS.includes(x.category))||(MODE=='local'&&!CAR_CATS.includes(x.category)))&&(!cat||x.category==cat)"
)
p.write_text(t)
print("toggle patched OK - cars: 8")
