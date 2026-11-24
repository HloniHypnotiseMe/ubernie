import pathlib
p = pathlib.Path("categories.html")
t = p.read_text()
# Insert hero <p> right after H1
t = t.replace(
    "<h1>UBERNIE Categories</h1>",
    "<h1>UBERNIE Categories</h1>\n<p>Browse all categories. 2,693 verified businesses across South Africa. Find it, compare it, book it.</p>"
)
p.write_text(t)
print("categories hero fixed")
