import pathlib, glob, re
sidebar_html = """<div id="sidebarOverlay"></div><aside id="sidebar" class="open"><button id="sidebarClose" onclick="toggleSidebar(false);return false;">✕ Close</button><h4>All Categories</h4><div><a href="category.html?cat=accommodation">accommodation</a></div><div><a href="category.html?cat=airbnb">airbnb</a></div><div><a href="category.html?cat=automotive">automotive</a></div><div><a href="category.html?cat=beauty">beauty</a></div><div><a href="category.html?cat=cafe">cafe</a></div><div><a href="category.html?cat=car-rental">car rental</a></div><div><a href="category.html?cat=car-repair">car repair</a></div><div><a href="category.html?cat=car-wash">car wash</a></div><div><a href="category.html?cat=day-care">day-care</a></div><div><a href="category.html?cat=dealership">dealership</a></div><div><a href="category.html?cat=education">education</a></div><div><a href="category.html?cat=electronics">electronics</a></div><div><a href="category.html?cat=fashion">fashion</a></div><div><a href="category.html?cat=fitness">fitness</a></div><div><a href="category.html?cat=food">food</a></div><div><a href="category.html?cat=grocery">grocery</a></div><div><a href="category.html?cat=hairdresser">hairdresser</a></div><div><a href="category.html?cat=health">health</a></div><div><a href="category.html?cat=hotel">hotel</a></div><div><a href="category.html?cat=liquor">liquor</a></div><div><a href="category.html?cat=mechanic">mechanic</a></div><div><a href="category.html?cat=pets">pets</a></div><div><a href="category.html?cat=pharmacy">pharmacy</a></div><div><a href="category.html?cat=property">property</a></div><div><a href="category.html?cat=restaurant">restaurant</a></div><div><a href="category.html?cat=services">services</a></div><div><a href="category.html?cat=spare-parts">spare parts</a></div><div><a href="category.html?cat=supermarket">supermarket</a></div><div><a href="category.html?cat=tyres">tyres</a></div></aside>"""
for f in glob.glob("*.html"):
    p=pathlib.Path(f); t=p.read_text(encoding="utf-8", errors="ignore"); orig=t
    if 'http-equiv="refresh"' in t: print(f"{f}: SKIP redirect"); continue
    # Remove old inline toggleSidebar function - use shared file only
    t=re.sub(r"function toggleSidebar\(force\)\{.*?\n\}", "", t, flags=re.DOTALL, count=1)
    # Add sidebar HTML if missing - right after <body>
    if 'id="sidebar"' not in t:
        t=re.sub(r"<body[^>]*>", lambda m: m.group(0)+sidebar_html, t, count=1)
    # Add CSS + JS if missing
    if 'sidebar.css' not in t and '</head>' in t:
        t=t.replace('</head>', '<link rel="stylesheet" href="sidebar.css"></head>', 1)
    if 'sidebar.js' not in t and '</body>' in t:
        t=t.replace('</body>', '<script src="sidebar.js"></script></body>', 1)
    # Ensure there's a menu button - add one after header if missing
    if 'id="menuBtn"' not in t:
        t=t.replace('</header>', '<button id="menuBtn" style="position:fixed;top:70px;left:10px;z-index:101;background:#111;color:#fff;border:0;padding:8px 12px;border-radius:6px;cursor:pointer">☰ Categories</button></header>', 1)
    if t!=orig: p.write_text(t, encoding="utf-8"); print(f"{f}: FIXED")
    else: print(f"{f}: OK")
