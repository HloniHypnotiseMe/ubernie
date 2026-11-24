import pathlib, re
p = pathlib.Path("day-care.html")
t = p.read_text()
print("BEFORE:", re.search(r'<title>.*?</title>', t, re.I|re.S).group(0))
# Replace title to include SGELA - keep rest same
t = re.sub(r'<title>.*?</title>', '<title>Ubernie Sgela | Day-Care South Africa - 17 Businesses</title>', t, count=1, flags=re.I|re.S)
p.write_text(t)
print("AFTER:", re.search(r'<title>.*?</title>', t, re.I|re.S).group(0))
