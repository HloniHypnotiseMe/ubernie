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
    }
}
