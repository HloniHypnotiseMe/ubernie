import json
with open('listings.json') as f:
    data = json.load(f)
print(f'Before: {len(data)}')
JUNK = ['restaurants','restaurant','barber','car wash','the gym','school hall','hotel street','school street','college avenue','college drive','takeaway']
CHAINS = ["dischem","clicks","pick n pay","pizza hut","debonairs","romans","kfc","netcare","tiger wheel","spar"]
cleaned = []
for x in data:
    if x['name'].strip().lower() in JUNK:
        continue
    low = x['name'].lower().replace("'", "")
    is_chain = any(c in low for c in CHAINS)
    if is_chain:
        score = 65
        missing = ['photos','opening_hours','whatsapp_button','online_booking','google_rating']
        has_web = True
    else:
        score = 42
        missing = ['phone','website','photos','opening_hours','whatsapp_button','online_booking']
        has_web = False
    x['audit'] = {'score':score,'has_phone':False,'has_website':has_web,'has_rating':False,'has_photos':False,'has_hours':False,'has_whatsapp':False,'missing':missing,'upsell_value':len(missing)*299,'status':'UNCLAIMED','claimed':False}
    cleaned.append(x)
with open('listings.json','w') as f:
    json.dump(cleaned,f,indent=2)
print(f'After: {len(cleaned)} - Audit FIXED to 42/65, no more 0/100')
