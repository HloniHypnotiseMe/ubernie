import pathlib, glob, re, json
# Find drinking category file - could be drinkingwell, drinking, bars
for f in glob.glob("*.html"):
    print(f)
# Load listings to find real category name
try:
    d=json.load(open('listings.json'))
    import collections
    print(collections.Counter([x.get('category') for x in d]))
except Exception as e:
    print("no listings", e)
