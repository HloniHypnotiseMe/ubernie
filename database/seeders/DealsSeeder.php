<?php
namespace Database\Seeders;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;
use Carbon\Carbon;

class DealsSeeder extends Seeder
{
    public function run(): void
    {
        $thursday = Carbon::now()->next(Carbon::THURSDAY)->setTime(0, 0);
        $sunday = $thursday->copy()->addDays(3)->setTime(23, 59);
        $deals = [
            ['KWMDC - FREE Tour + R500 Off Registration', 'KWMDC', 'KWMDC-TOUR-FREE', 500, 500, 'thursday_deal'],
            ['Car-La-Hurry - R2,000 Off Any Bakkie This Thursday', 'Car-La-Hurry', 'CARLAHURRY-2000', 2000, 2000, 'thursday_deal'],
            ['Fresh Cut - R20 Off Cut + Wash', 'Fresh Cut', 'FRESHCUT-20', 20, 20, 'voucher'],
            ['eKhaya - FREE Viewing + No Admin Fee', 'eKhaya', 'EKHAYA-FREE-VIEW', 0, 0, 'thursday_deal'],
            ['Beauty - 20% Off Nails Thursday Only', 'Beauty', 'BEAUTY-20PCT', 20, 20, 'thursday_deal'],
        ];
        foreach ($deals as [$title, $biz, $code, $orig, $deal, $type]) {
            $b = DB::table('businesses')->where('name', 'like', '%' . explode(' -', $biz)[0] . '%')->first();
            if (!$b) continue;
            DB::table('deals')->updateOrInsert(
                ['voucher_code' => $code],
                [
                    'business_id' => $b->id,
                    'category_id' => $b->category_id,
                    'title' => $title,
                    'slug' => Str::slug($title),
                    'description' => $title,
                    'voucher_code' => $code,
                    'original_price' => $orig,
                    'deal_price' => $deal,
                    'discount_percent' => 20,
                    'deal_type' => $type,
                    'starts_at' => $thursday,
                    'ends_at' => $sunday,
                    'max_redemptions' => 100,
                    'redemptions_count' => 0,
                    'status' => 'approved',
                    'featured' => true,
                    'updated_at' => now(),
                    'created_at' => now(),
                ]
            );
        }
    }
}
