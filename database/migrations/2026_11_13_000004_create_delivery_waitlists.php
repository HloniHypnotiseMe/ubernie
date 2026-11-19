<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
return new class extends Migration {
    public function up(): void {
        // 1. Shops waiting for delivery
        Schema::create('delivery_waitlist_shops', function (Blueprint $table) {
            $table->id();
            $table->string('business_name');
            $table->string('owner_name')->nullable();
            $table->string('phone');
            $table->string('whatsapp')->nullable();
            $table->string('category_slug')->nullable();
            $table->string('area');
            $table->string('city')->default('Johannesburg');
            $table->decimal('lat', 10, 7)->nullable();
            $table->decimal('lng', 10, 7)->nullable();
            $table->boolean('has_own_drivers')->default(false);
            $table->integer('avg_orders_per_day')->nullable();
            $table->enum('status', ['waiting','unlocked','launched','rejected'])->default('waiting');
            $table->timestamps();
            $table->index(['area','status']);
            $table->index(['city','status']);
        });
        // 2. Drivers / Riders waiting to deliver
        Schema::create('delivery_waitlist_drivers', function (Blueprint $table) {
            $table->id();
            $table->string('full_name');
            $table->string('phone');
            $table->string('whatsapp')->nullable();
            $table->string('id_number')->nullable();
            $table->enum('vehicle_type', ['bicycle','motorbike','car','bakkie','on_foot'])->default('motorbike');
            $table->string('licence_plate')->nullable();
            $table->string('area');
            $table->string('city')->default('Johannesburg');
            $table->decimal('lat', 10, 7)->nullable();
            $table->decimal('lng', 10, 7)->nullable();
            $table->string('available_hours')->nullable();
            $table->boolean('has_licence')->default(false);
            $table->boolean('has_pdp')->default(false);
            $table->enum('status', ['waiting','verified','approved','active','suspended','rejected'])->default('waiting');
            $table->timestamps();
            $table->index(['area','status']);
            $table->index(['vehicle_type','status']);
        });
        // 3. Demand Zones - Uber Surge Logic, But For Delivery
        Schema::create('delivery_demand_zones', function (Blueprint $table) {
            $table->id();
            $table->string('area');
            $table->string('city')->default('Johannesburg');
            $table->integer('shops_waiting')->default(0);
            $table->integer('shops_live')->default(0);
            $table->integer('drivers_waiting')->default(0);
            $table->integer('drivers_live')->default(0);
            $table->integer('active_orders')->default(0);
            $table->decimal('demand_multiplier', 3, 2)->default(1.00);
            $table->integer('base_delivery_fee_cents')->default(2000);
            $table->integer('current_delivery_fee_cents')->default(2000);
            $table->enum('zone_status', ['waiting','unlock_soon','unlocked','live','paused'])->default('waiting');
            $table->integer('unlock_threshold_shops')->default(10);
            $table->integer('unlock_threshold_drivers')->default(10);
            $table->timestamps();
            $table->unique(['area','city']);
        });
    }
    public function down(): void {
        Schema::dropIfExists('delivery_demand_zones');
        Schema::dropIfExists('delivery_waitlist_drivers');
        Schema::dropIfExists('delivery_waitlist_shops');
    }
};
