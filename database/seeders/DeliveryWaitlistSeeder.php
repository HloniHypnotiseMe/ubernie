<?php
namespace Database\Seeders;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
class DeliveryWaitlistSeeder extends Seeder {
    public function run(): void {
        // Roodepoort - First Launch Zone
        DB::table('delivery_demand_zones')->updateOrInsert(
            ['area'=>'Roodepoort','city'=>'Johannesburg'],
            ['area'=>'Roodepoort','city'=>'Johannesburg','shops_waiting'=>3,'shops_live'=>0,'drivers_waiting'=>2,'drivers_live'=>0,'active_orders'=>0,'demand_multiplier'=>1.00,'base_delivery_fee_cents'=>2000,'current_delivery_fee_cents'=>2000,'zone_status'=>'waiting','unlock_threshold_shops'=>10,'unlock_threshold_drivers'=>10,'updated_at'=>now(),'created_at'=>now()]
        );
        DB::table('delivery_demand_zones')->updateOrInsert(
            ['area'=>'Soweto','city'=>'Johannesburg'],
            ['area'=>'Soweto','city'=>'Johannesburg','shops_waiting'=>1,'shops_live'=>0,'drivers_waiting'=>1,'drivers_live'=>0,'active_orders'=>0,'demand_multiplier'=>1.00,'base_delivery_fee_cents'=>2000,'current_delivery_fee_cents'=>2000,'zone_status'=>'waiting','unlock_threshold_shops'=>10,'unlock_threshold_drivers'=>10,'updated_at'=>now(),'created_at'=>now()]
        );
        // Example shops waiting
        $shops = [
            ['KWMDC Tuck Shop','0837238576','Roodepoort','day-care-creche'],
            ['Fresh Cut Barbers - Products','0830000001','Roodepoort','beauty-salons-barbers'],
            ['Car-La-Hurry Parts','0830000002','Roodepoort','automotive'],
        ];
        foreach ($shops as [$name,$phone,$area,$cat]) {
            DB::table('delivery_waitlist_shops')->updateOrInsert(
                ['phone'=>$phone],
                ['business_name'=>$name,'phone'=>$phone,'whatsapp'=>$phone,'category_slug'=>$cat,'area'=>$area,'city'=>'Johannesburg','has_own_drivers'=>false,'avg_orders_per_day'=>5,'status'=>'waiting','updated_at'=>now(),'created_at'=>now()]
            );
        }
        // Example drivers waiting
        $drivers = [
            ['Thabo M','0830000010','motorbike','Roodepoort'],
            ['Sipho K','0830000011','car','Roodepoort'],
            ['Lerato D','0830000012','bicycle','Soweto'],
        ];
        foreach ($drivers as [$name,$phone,$veh,$area]) {
            DB::table('delivery_waitlist_drivers')->updateOrInsert(
                ['phone'=>$phone],
                ['full_name'=>$name,'phone'=>$phone,'whatsapp'=>$phone,'vehicle_type'=>$veh,'area'=>$area,'city'=>'Johannesburg','available_hours'=>'09:00-21:00','has_licence'=>true,'has_pdp'=>false,'status'=>'waiting','updated_at'=>now(),'created_at'=>now()]
            );
        }
    }
}
