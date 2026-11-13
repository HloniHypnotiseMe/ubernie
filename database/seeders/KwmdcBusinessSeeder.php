<?php
namespace Database\Seeders;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
class KwmdcBusinessSeeder extends Seeder
{
    public function run(): void
    {
        $cat = DB::table('categories')->where('slug','day-care-creche')->first();
        $user = DB::table('users')->first(); // Admin / owner - replace with real user_id
        if (!$cat || !$user) return;
        DB::table('businesses')->updateOrInsert(
            ['slug'=>'kids-with-a-mission-day-care-roodepoort'],
            [
                'user_id'=>$user->id,
                'name'=>'Kids With A Mission Day Care (KWMDC)',
                'slug'=>'kids-with-a-mission-day-care-roodepoort',
                'category_id'=>$cat->id,
                'description'=>'Looking for a Daycare in Roodepoort? KWMDC is a trusted Daycare, Creche & Aftercare in Roodepoort for ages 6 Months to 6 Years. Open Mon-Fri 6am-6pm. 4 Meals Included. Qualified ECD Practitioners. Book a FREE Tour - WhatsApp 083 723 8576.',
                'address'=>'Roodepoort, Gauteng',
                'lat'=>-26.1625, 'lng'=>27.8725,
                'phone'=>'0837238576',
                'email'=>'info@kwmdc.co.za',
                'website'=>'https://kwmdc.hlonihypnotiseme.co.za',
                'logo'=>null,
                'status'=>'approved',
                'featured'=>true,
                'updated_at'=>now(),'created_at'=>now(),
            ]
        );
    }
}
