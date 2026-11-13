<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
return new class extends Migration {
    public function up(): void {
        Schema::table('businesses', function (Blueprint $table) {
            // 1. Uber Geo Matching - ETA, distance, service area
            $table->decimal('service_radius_km', 6, 2)->default(10)->after('lng');
            $table->integer('avg_response_minutes')->nullable()->after('service_radius_km');
            $table->boolean('offers_delivery')->default(false)->after('avg_response_minutes');
            $table->boolean('offers_mobile_service')->default(false)->after('offers_delivery');
            // 4. Two-Way Ratings
            $table->decimal('rating_avg', 3, 2)->default(0)->after('featured');
            $table->integer('rating_count')->default(0)->after('rating_avg');
            $table->decimal('customer_rating_avg', 3, 2)->default(0)->after('rating_count');
            // 5. Verified Badge + OTP Claim
            $table->enum('verification_status', ['unverified','otp_verified','id_verified','cipc_verified','rmi_verified'])->default('unverified')->after('customer_rating_avg');
            $table->string('verification_badge')->nullable()->after('verification_status');
            $table->dateTime('verified_at')->nullable()->after('verification_badge');
            // 9. Uber One Equivalent - Featured Tier
            $table->string('tier')->default('free')->after('verified_at');
            $table->boolean('is_featured_deals')->default(false)->after('tier');
            // 10. Uber for Business - Multi-location
            $table->string('parent_business_id')->nullable()->after('is_featured_deals');
            $table->string('branch_name')->nullable()->after('parent_business_id');
            // 3. Share + Live
            $table->string('share_slug')->nullable()->unique()->after('branch_name');
            $table->string('whatsapp_number')->nullable()->after('share_slug');
            $table->string('booking_url')->nullable()->after('whatsapp_number');
        });
        // 8. Lead State Machine - Uber Trip State Machine for Ubernie
        Schema::create('leads', function (Blueprint $table) {
            $table->id();
            $table->foreignId('business_id')->constrained()->cascadeOnDelete();
            $table->foreignId('category_id')->nullable()->constrained()->nullOnDelete();
            $table->string('customer_name')->nullable();
            $table->string('customer_phone');
            $table->string('customer_whatsapp')->nullable();
            $table->text('message')->nullable();
            $table->string('source')->default('ubernie_directory');
            $table->enum('status', ['inquiry','replied','tour_booked','showed','no_show','paid','reviewed','cancelled'])->default('inquiry');
            $table->dateTime('replied_at')->nullable();
            $table->dateTime('tour_at')->nullable();
            $table->dateTime('paid_at')->nullable();
            $table->decimal('deal_amount', 10, 2)->nullable();
            $table->string('voucher_code_used')->nullable();
            $table->integer('customer_rating')->nullable();
            $table->integer('business_rating')->nullable();
            $table->timestamps();
            $table->index(['business_id','status']);
            $table->index(['customer_phone','status']);
        });
    }
    public function down(): void {
        Schema::dropIfExists('leads');
        Schema::table('businesses', function (Blueprint $table) {
            $table->dropColumn(['service_radius_km','avg_response_minutes','offers_delivery','offers_mobile_service','rating_avg','rating_count','customer_rating_avg','verification_status','verification_badge','verified_at','tier','is_featured_deals','parent_business_id','branch_name','share_slug','whatsapp_number','booking_url']);
        });
    }
};
