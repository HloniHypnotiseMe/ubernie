<?php
namespace Database\Seeders;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

class CategorySeeder extends Seeder
{
    public function run(): void
    {
        // Parent: Day Care & Creche - Category #1 for Daycare Business-in-a-Box
        $parentId = DB::table('categories')->updateOrInsert(
            ['slug' => 'day-care-creche'],
            [
                'name' => 'Day Care & Creche',
                'slug' => 'day-care-creche',
                'parent_id' => null,
                'icon' => '👶',
                'color' => '#FF6B35',
                'description' => 'Daycares, creches, ECD centres, preschools, aftercare and nursery schools',
                'seo_title' => 'Daycare, Creche & Aftercare in {city} | Ubernie',
                'seo_description' => 'Find trusted Daycares, Creches, ECD Centres and Aftercare in {city}. Ages 6 Months - 6 Years. 4 Meals, Qualified Teachers, Book a FREE Tour on Ubernie.',
                'featured' => true,
                'is_active' => true,
                'sort_order' => 1,
                'listing_fields' => json_encode([
                    ['key'=>'ages','label'=>'Ages Accepted','type'=>'text','placeholder'=>'6 Months - 6 Years'],
                    ['key'=>'hours','label'=>'Hours','type'=>'text','placeholder'=>'Mon-Fri 6am-6pm'],
                    ['key'=>'fees_from','label'=>'Fees From (R/month)','type'=>'number'],
                    ['key'=>'meals_included','label'=>'Meals Included?','type'=>'checkbox'],
                    ['key'=>'whatsapp','label'=>'WhatsApp Number','type'=>'phone'],
                    ['key'=>'programs','label'=>'Programs','type'=>'multiselect'],
                ]),
                'updated_at' => now(), 'created_at' => now(),
            ]
        );

        $parent = DB::table('categories')->where('slug','day-care-creche')->first();

        $subs = [
            ['Daycare','daycare',2], ['Creche','creche',3], ['ECD Centre','ecd-centre',4],
            ['Preschool / Nursery School','preschool',5], ['Aftercare','aftercare',6],
            ['Baby Care (0-18m)','baby-care',7], ['Grade R','grade-r',8], ['Holiday Care','holiday-care',9],
        ];
        foreach ($subs as [$name,$slug,$order]) {
            DB::table('categories')->updateOrInsert(
                ['slug'=>$slug],
                ['name'=>$name,'slug'=>$slug,'parent_id'=>$parent->id,'icon'=>'👶','color'=>'#FF6B35','description'=>$name.' in Day Care & Creche category','featured'=>false,'is_active'=>true,'sort_order'=>$order,'updated_at'=>now(),'created_at'=>now()]
            );
        }

        // Second parent: Funeral / Hearse Trailers - keeps your other offer
        DB::table('categories')->updateOrInsert(
            ['slug'=>'funeral-services'],
            ['name'=>'Funeral Services & Hearse Trailers','slug'=>'funeral-services','parent_id'=>null,'icon'=>'⚰️','color'=>'#000000','description'=>'Funeral parlours, hearse trailers, rent-to-own trailers','seo_title'=>'Hearse Trailers & Funeral Services in Gauteng | Ubernie','seo_description'=>'Premium hearse trailers in Gauteng. From R75k. Rent-To-Own available. Nationwide delivery.','featured'=>true,'is_active'=>true,'sort_order'=>2,'updated_at'=>now(),'created_at'=>now()]
        );

        // --- WAVE 2: Automotive, BBLA, Property, Beauty, Malls ---
        $wave2 = [
            ['Automotive & Car-La-Hurry','automotive','🚗','#1D3557','Car dealerships, car sales, car wash, panel beaters, tyres, parts, mechanics, bakkies, taxis','Car Dealerships & Automotive in {city} | Ubernie','Find Car Dealerships, Car Sales, Panel Beaters, Tyres, Parts & Mechanics in {city}. From R0 to R3.6M. Finance available.',3,'🚗'],
            ['Black Business Locator App','black-business-locator','✊','#000000','Black-owned businesses across SA - BBLA tenant on Ubernie engine','Black Owned Businesses in {city} | BBLA on Ubernie','Find Black-Owned Businesses in {city}. Support local. BBLA - Black Business Locator App on Ubernie.',4,'✊'],
            ['eKhaya - Property & Real Estate','property','🏠','#2A9D8F','Houses, flats, rentals, stands, commercial property - eKhaya','Property & Houses To Rent in {city} | eKhaya on Ubernie','Find Houses, Flats, Rentals & Stands in {city}. eKhaya - Property on Ubernie. No AI slop, just real listings.',5,'🏠'],
            ['Beauty, Salons & Barbers','beauty-salons-barbers','💇','#9B5DE5','Hair salons, barbers, nails, beauty, makeup, spa','Hair Salons, Barbers & Beauty in {city} | Ubernie','Find Hair Salons, Barbers, Nails & Beauty in {city}. Fresh Cut, Fresh Start. Book on WhatsApp.',6,'💇'],
            ['Shopping Malls & Complexes','shopping-malls','🛍️','#F77F00','Malls, shopping centres, complexes, markets','Shopping Malls in {city} | Ubernie','Find Shopping Malls, Centres & Complexes in {city}. Stores, deals, opening hours.',7,'🛍️'],
            ['Food, Groceries & Takeaways','food-groceries','🍔','#E63946','Restaurants, takeaways, spaza, butchery, groceries - Thursday Deals home','Food & Grocery Deals in {city} | Ubernie Thursday Deals','Find Restaurants, Takeaways & Grocery Deals in {city}. Thursday Deals live every Thursday.',8,'🍔'],
            ['Clothing, Fashion & Tech','fashion-tech','👗','#FF6B35','Clothing, fashion, phones, laptops, electronics - Top searched in SA','Clothing & Tech Deals in {city} | Ubernie','Find Clothing, Fashion, Phones & Laptops in {city}. Top searched categories in SA.',9,'👗'],
        ];
        foreach ($wave2 as [$name,$slug,$icon,$color,$desc,$seoTitle,$seoDesc,$order,$ic]) {
            DB::table('categories')->updateOrInsert(
                ['slug'=>$slug],
                ['name'=>$name,'slug'=>$slug,'parent_id'=>null,'icon'=>$icon,'color'=>$color,'description'=>$desc,'seo_title'=>$seoTitle,'seo_description'=>$seoDesc,'featured'=>true,'is_active'=>true,'sort_order'=>$order,'updated_at'=>now(),'created_at'=>now()]
            );
        }

        // --- Automotive Subcategories ---
        $auto = DB::table('categories')->where('slug','automotive')->first();
        if ($auto) {
            $subs = [
                ['Car Dealerships','car-dealerships',1],['Used Cars','used-cars',2],['Bakkies & SUVs','bakkies-suvs',3],
                ['Car Wash','car-wash',4],['Panel Beaters & Spray Painters','panel-beaters',5],['Tyres & Batteries','tyres-batteries',6],
                ['Mechanics & Services','mechanics',7],['Car Parts & Accessories','car-parts',8],['Taxis & Transport','taxis-transport',9],
            ];
            foreach ($subs as [$n,$s,$o]) {
                DB::table('categories')->updateOrInsert(['slug'=>$s],['name'=>$n,'slug'=>$s,'parent_id'=>$auto->id,'icon'=>'🚗','color'=>'#1D3557','description'=>$n,'featured'=>false,'is_active'=>true,'sort_order'=>$o,'updated_at'=>now(),'created_at'=>now()]);
            }
        }

        // --- Beauty Subcategories ---
        $beauty = DB::table('categories')->where('slug','beauty-salons-barbers')->first();
        if ($beauty) {
            $subs = [
                ['Hair Salon','hair-salon',1],['Barber Shop','barber-shop',2],['Nails','nails',3],
                ['Makeup','makeup',4],['Spa & Massage','spa-massage',5],['Tattoos & Piercing','tattoos',6],
            ];
            foreach ($subs as [$n,$s,$o]) {
                DB::table('categories')->updateOrInsert(['slug'=>$s],['name'=>$n,'slug'=>$s,'parent_id'=>$beauty->id,'icon'=>'💇','color'=>'#9B5DE5','description'=>$n,'featured'=>false,'is_active'=>true,'sort_order'=>$o,'updated_at'=>now(),'created_at'=>now()]);
            }
        }

        // --- Property Subcategories (eKhaya) ---
        $prop = DB::table('categories')->where('slug','property')->first();
        if ($prop) {
            $subs = [
                ['Houses For Sale','houses-for-sale',1],['Flats To Rent','flats-to-rent',2],['Houses To Rent','houses-to-rent',3],
                ['Stands & Land','stands-land',4],['Commercial Property','commercial-property',5],['Estate Agents','estate-agents',6],
            ];
            foreach ($subs as [$n,$s,$o]) {
                DB::table('categories')->updateOrInsert(['slug'=>$s],['name'=>$n,'slug'=>$s,'parent_id'=>$prop->id,'icon'=>'🏠','color'=>'#2A9D8F','description'=>$n,'featured'=>false,'is_active'=>true,'sort_order'=>$o,'updated_at'=>now(),'created_at'=>now()]);
            }
        }

    }
}
