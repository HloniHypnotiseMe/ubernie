<?php
namespace Database\Seeders;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
class BusinessInABoxSeeder extends Seeder {
    public function run(): void {
        $biz = DB::table('businesses')->where('name','like','%KWMDC%')->first();
        DB::table('business_in_a_box_orders')->updateOrInsert(
            ['owner_phone'=>'0837238576'],
            ['business_name'=>'KWMDC','owner_name'=>'KWMDC Owner','owner_phone'=>'0837238576','owner_email'=>null,'industry'=>'daycare','category_slug'=>'day-care-creche','area'=>'Roodepoort','city'=>'Johannesburg','once_off_cents'=>950000,'monthly_cents'=>75000,'payment_link_id'=>null,'payment_status'=>'paid','provision_status'=>'completed','website_url'=>'https://kwmdc.ubernie.co.za','listing_url'=>'https://ubernie.co.za/business/kwmdc','shop_app_url'=>'https://app.ubernie.co.za/shop','business_id'=>$biz?->id,'paid_at'=>now()->subDays(5),'provisioned_at'=>now()->subDays(5),'provision_error'=>null,'updated_at'=>now(),'created_at'=>now()->subDays(5)]
        );
    }
}
