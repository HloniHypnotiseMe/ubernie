import pathlib, re
HERO = {
 # CAR-LA-HURRY - cars only
 "automotive.html": "Find verified mechanics, dealerships, car wash, tyres and spare parts near you. Compare prices, read reviews, book in 2 minutes. 35+ Automotive businesses across 9 provinces.",
 "mechanic.html": "Find verified mechanics near you. Compare quotes, read reviews, book a service in 2 minutes. 285 mechanics across South Africa.",
 "dealership.html": "Browse verified car dealerships near you. Compare stock, prices and reviews. 242 dealerships across South Africa.",
 "car-rental.html": "Compare verified car rental near you. Prices, reviews, pick-up locations. 60 rental businesses across South Africa.",
 "car-repair.html": "Find verified car repair near you. Compare quotes, read reviews, book in 2 minutes. 85 repair shops.",
 "car-wash.html": "Find verified car wash near you. Prices, reviews, locations. 40 car washes across South Africa.",
 "tyres.html": "Find verified tyre shops near you. Compare prices, fitment, reviews. 60 tyre shops.",
 "spare-parts.html": "Find verified spare parts suppliers near you. Compare prices, stock, reviews. 159 suppliers.",
 # IDLA NATHI - food only
 "restaurant.html": "Find verified restaurants near you. Menus, reviews, prices. 240 restaurants - from kota to fine dining. Book a table in 2 minutes.",
 "cafe.html": "Find verified cafes near you. Menus, coffee, reviews. 181 cafes across South Africa.",
 "food.html": "Find verified food businesses near you. Takeaways, catering, groceries. 93 businesses.",
 # SGELA - education only
 "education.html": "Find verified schools, colleges and tutors near you. Compare fees, reviews, results. 216 education businesses.",
 "day-care.html": "Find verified day-care and creches near you. Compare fees, reviews, safety. 17 day-cares across South Africa.",
 # BUHLE
 "beauty.html": "Find verified beauty salons near you. Nails, makeup, facials. 48 beauty businesses.",
 "hairdresser.html": "Find verified hairdressers near you. Cuts, braids, weaves, treatments. 82 hairdressers.",
 # SDWADLO
 "fashion.html": "Find verified fashion boutiques near you. Clothes, shoes, tailoring. 10 fashion businesses.",
 # DRINKINGWELL
 "drinkingwell.html": "Find verified bars, pubs and taverns near you. Specials, events, reviews. Drink responsibly.",
 "liquor.html": "Find verified liquor stores near you. Prices, specials, delivery. 13 liquor stores.",
 # LAST REST
 "funeral.html": "Find verified funeral services near you. Respectful, affordable, transparent pricing. Compare plans and reviews.",
 # UBERNIE core
 "accommodation.html": "Find verified accommodation near you. Guesthouses, B&Bs, lodges. 105 businesses.",
 "airbnb.html": "Find verified Airbnb hosts near you. Compare prices, reviews. 19 listings.",
 "hotel.html": "Find verified hotels near you. Compare prices, reviews, amenities. 142 hotels.",
 "health.html": "Find verified health providers near you. Clinics, dentists, doctors. 168 providers.",
 "pharmacy.html": "Find verified pharmacies near you. Prices, delivery, reviews. 95 pharmacies.",
 "grocery.html": "Find verified grocery stores near you. Prices, specials, delivery. 73 stores.",
 "supermarket.html": "Find verified supermarkets near you. Prices, specials, delivery. 162 supermarkets.",
 "fitness.html": "Find verified gyms and fitness studios near you. Prices, classes, reviews. 20 gyms.",
 "pets.html": "Find verified pet services near you. Vets, grooming, boarding. 6 pet businesses.",
 "property.html": "Find verified property agents near you. Rentals, sales, reviews. 23 agencies.",
 "services.html": "Find verified local services near you. Plumbers, electricians, cleaners. 13 services.",
 "electronics.html": "Find verified electronics stores near you. Prices, repairs, reviews. 1 store - more coming.",
 "index.html": "South Africa's trusted marketplace. 2,693 verified businesses across 9 provinces. Find it, compare it, book it - in 2 minutes.",
 "deals.html": "Verified vouchers & discounts from South African businesses. Claim a voucher, save money, support local.",
 "categories.html": "Browse all categories. 2,693 verified businesses across South Africa.",
}
for fname, hero in HERO.items():
    p = pathlib.Path(fname)
    if not p.exists(): continue
    t = p.read_text()
    # Replace first hero <p> after first <h1>
    m = re.search(r'(<h1[^>]*>.*?</h1>\s*<p>)(.*?)(</p>)', t, re.I|re.S)
    if m:
        t = t[:m.start(2)] + hero + t[m.end(2):]
        p.write_text(t)
        print(f"fixed hero {fname}")
    else:
        print(f"NO HERO P {fname} - check manually")
