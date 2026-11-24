<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
return new class extends Migration {
    public function up(): void {
        // Smart Drinker Drivers - Chauffeurs who drive YOU home in YOUR car
        Schema::create('smart_drinker_drivers', function (Blueprint $table) {
            $table->id();
            $table->string('full_name');
            $table->string('phone');
            $table->string('whatsapp')->nullable();
            $table->string('id_number_hash')->nullable();
            $table->string('licence_number_hash')->nullable();
            $table->boolean('has_pdp')->default(false);
            $table->boolean('has_insurance')->default(false);
            $table->string('area');
            $table->string('city')->default('Johannesburg');
            $table->decimal('lat', 10, 7)->nullable();
            $table->decimal('lng', 10, 7)->nullable();
            $table->boolean('is_online')->default(false);
            $table->decimal('rating_avg', 3, 2)->default(0);
            $table->integer('trips_completed')->default(0);
            $table->enum('status', ['pending','verified','approved','active','suspended','rejected'])->default('pending');
            $table->timestamps();
            $table->index(['area','is_online','status']);
        });
        // Smart Drinker Bookings - Take Me Home
        Schema::create('smart_drinker_bookings', function (Blueprint $table) {
            $table->id();
            $table->foreignId('business_id')->nullable()->constrained()->nullOnDelete();
            $table->string('customer_name');
            $table->string('customer_phone');
            $table->string('customer_whatsapp')->nullable();
            $table->string('pickup_location');
            $table->decimal('pickup_lat', 10, 7)->nullable();
            $table->decimal('pickup_lng', 10, 7)->nullable();
            $table->string('dropoff_location');
            $table->decimal('dropoff_lat', 10, 7)->nullable();
            $table->decimal('dropoff_lng', 10, 7)->nullable();
            $table->decimal('distance_km', 6, 2)->nullable();
            $table->string('car_make')->nullable();
            $table->string('car_model')->nullable();
            $table->string('car_plate')->nullable();
            $table->enum('car_type', ['sedan','bakkie','suv','luxury'])->default('sedan');
            $table->integer('passengers')->default(1);
            $table->boolean('needs_buddy_driver')->default(false);
            $table->string('otp_code', 6)->nullable();
            $table->foreignId('driver_id')->nullable()->constrained('smart_drinker_drivers')->nullOnDelete();
            $table->foreignId('buddy_driver_id')->nullable()->constrained('smart_drinker_drivers')->nullOnDelete();
            $table->integer('base_price_cents')->default(15000);
            $table->decimal('demand_multiplier', 3, 2)->default(1.00);
            $table->integer('final_price_cents')->default(15000);
            $table->string('payment_link_id')->nullable();
            $table->enum('payment_status', ['pending','paid','failed','refunded'])->default('pending');
            $table->enum('status', ['requested','matched','driver_en_route','otp_verified','on_trip','completed','cancelled','no_show'])->default('requested');
            $table->dateTime('requested_at')->nullable();
            $table->dateTime('matched_at')->nullable();
            $table->dateTime('picked_up_at')->nullable();
            $table->dateTime('completed_at')->nullable();
            $table->integer('customer_rating')->nullable();
            $table->integer('driver_rating')->nullable();
            $table->string('share_token')->nullable()->unique();
            $table->timestamps();
            $table->index(['status','pickup_location']);
            $table->index(['driver_id','status']);
        });
    }
    public function down(): void {
        Schema::dropIfExists('smart_drinker_bookings');
        Schema::dropIfExists('smart_drinker_drivers');
    }
};
