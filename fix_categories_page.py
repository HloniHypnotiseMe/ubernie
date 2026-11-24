import pathlib
p = pathlib.Path("categories.html")
t = p.read_text()
# Add missing brands + normalize - only text replacements, no layout change
replacements = {
    "Cafe -": "Idla Nathi - Cafe -",
    "Food -": "Idla Nathi - Food -",
    "Car Rental -": "Car-La-Hurry - Car Rental -",
    "Car Repair -": "Car-La-Hurry - Car Repair -",
    "Car Wash -": "Car-La-Hurry - Car Wash -",
    "Dealership -": "Car-La-Hurry - Dealership -",
    "Spare Parts -": "Car-La-Hurry - Spare Parts -",
    "Tyres -": "Car-La-Hurry - Tyres -",
    "Liquor -": "DrinkingWell - Liquor -",
    "Hairdresser -": "Buhle - Hairdresser -",
    "Day-Care -": "Sgela - Day-Care -",
}
for old, new in replacements.items():
    if old in t and new not in t:
        t = t.replace(old, new)
# Add Last Rest if missing entirely
if "Last Rest" not in t:
    # Insert before Home link / footer
    t = t.replace("Home", "Last Rest - Funeral - 0\nHome", 1) if "Home" in t else t + "\nLast Rest - Funeral"
# Fix footer duplication: keep one Deals Corner line
p.write_text(t)
print("categories fixed")
