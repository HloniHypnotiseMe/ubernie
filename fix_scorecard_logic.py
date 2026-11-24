import pathlib
p = pathlib.Path("audit_scorecard.py")
t = p.read_text()
# deals.html should not need to link to itself
t = t.replace(
    'checks["6_Deals_Link"] = 1 if "deals.html" in t else 0',
    'checks["6_Deals_Link"] = 1 if ("deals.html" in t or fname=="deals.html") else 0'
)
p.write_text(t)
print("scorecard fixed")
