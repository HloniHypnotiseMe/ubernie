html=open('index.html').read()

old='<select id="area" onchange="render()"><option value="">All Areas - South Africa</option></select>'
new=old+'<select id="province" onchange="render()"><option value="">All Provinces</option></select>'
assert old in html, 'Area dropdown not found'
html=html.replace(old, new)

# Populate provinces - find the line by a short unique piece, no $ escaping
import re
m=re.search(r"document\.getElementById\('area'\)\.innerHTML=.*?\n", html)
assert m, 'Area populate line not found'
line=m.group(0)
add="let provinces=[...new Set(j.map(x=>x.province||'Unknown'))].sort(); document.getElementById('province').innerHTML='<option value=\"\">All Provinces</option>'+provinces.map(p=>`<option>${p}</option>`).join('');\n"
html=html.replace(line, line+add)

old3="let f=data.filter(x=>(!c||x.category===c)&&(!a||x.area===a)"
assert old3 in html, 'render filter not found'
html=html.replace(old3, "let pv=document.getElementById('province').value; let f=data.filter(x=>(!c||x.category===c)&&(!a||x.area===a)&&(!pv||x.province===pv)")

old4="document.getElementById('area').addEventListener('change',render);"
html=html.replace(old4, old4+" document.getElementById('province').addEventListener('change',render);")

open('index.html','w').write(html)
print('PROVINCE ADDED OK')
