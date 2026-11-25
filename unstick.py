import pathlib
p = pathlib.Path('index.html').read_text()
# Remove the broken filterByLocation + populateFilters + wrappers - all of it
import re
# Remove filterByLocation function
p = re.sub(r'function filterByLocation\(\)\{.*?\n\}\n', '', p, flags=re.DOTALL)
p = re.sub(r'// ===== PROVINCE.*?\n', '', p, flags=re.DOTALL)
p = re.sub(r'function getUnique.*?function onMetroChange.*?populateFilters\(\); filterByLocation\(\);\n\}', '', p, flags=re.DOTALL)
# Restore simple dropdowns: they just call render()
p = p.replace('onchange="onProvinceChange()"', 'onchange="render()"')
p = p.replace('onchange="onMetroChange()"', 'onchange="render()"')
p = p.replace('onchange="filterByLocation()"', 'onchange="render()"')
pathlib.Path('index.html').write_text(p)
print("✅ Unstuck - removed broken filter loop")
print("Page will now load again. Filters will be simple for now, we rebuild them clean next.")
