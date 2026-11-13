<?php
namespace Database\Seeders;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;
class SmartDrinkerSeeder extends Seeder {
    public function run(): void {
        // First Smart Drinker Drivers - Roodepoort Launch
        $drivers = [
            ['Mandla T','0830000020','Roodepoort',4.9,120],
            ['John S','0830000021','Roodepoort',4.8,95],
            ['Sipho N','0830000022','Soweto',4.9,80],
        ];
        foreach ($drivers as [$name,$phone,$area,$rating,$trips]) {
            DB::table('smart_drinker_drivers')->updateOrInsert(
                ['phone'=>$phone],
                ['full_name'=>$name,'phone'=>$phone,'whatsapp'=>$phone,'has_pdp'=>true,'has_insurance'=>true,'area'=>$area,'city'=>'Johannesburg','is_online'=>true,'rating_avg'=>$rating,'trips_completed'=>$trips,'status'=>'approved','updated_at'=>now(),'created_at'=>now()]
            );
        }
        // Example Booking - Demo, not real customer
        $driver = DB::table('smart_drinker_drivers')->where('phone','0830000020')->first();
        if ($driver) {
            DB::table('smart_drinker_bookings')->updateOrInsert(
                ['customer_phone'=>'0830000099'],
                ['business_id'=>null,'customer_name'=>'Demo Customer','customer_phone'=>'0830000099','customer_whatsapp'=>'0830000099','pickup_location'=>'Roodepoort - Drinking Well Tavern','dropoff_location'=>'Roodepoort - Home','distance_km'=>8.5,'car_make'=>'Toyota','car_model'=>'Corolla','car_plate'=>'DEMO-123','car_type'=>'sedan','passengers'=>1,'needs_buddy_driver'=>false,'otp_code'=>'123456','driver_id'=>$driver->id,'buddy_driver_id'=>null,'base_price_cents'=>15000,'demand_multiplier'=>1.00,'final_price_cents'=>15000,'payment_link_id'=>null,'payment_status'=>'pending','status'=>'completed','requested_at'=>now()->subHours(2),'matched_at'=>now()->subHours(2),'picked_up_at'=>now()->subHours(1),'completed_at'=>now()->subHour(1),'customer_rating'=>5,'driver_rating'=>5,'share_token'=>Str::random(12),'updated_at'=>now(),'created_at'=>now()->subHours(2)]
            );
        }
    }
}
