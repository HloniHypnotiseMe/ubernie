<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
return new class extends Migration {
    public function up(): void {
        Schema::create('business_in_a_box_orders', function (Blueprint $table) {
            $table->id();
            $table->string('business_name');
            $table->string('owner_name')->nullable();
            $table->string('owner_phone');
            $table->string('owner_email')->nullable();
            $table->string('industry');
            $table->string('category_slug');
            $table->string('area');
            $table->string('city')->default('Johannesburg');
            $table->integer('once_off_cents')->default(950000);
            $table->integer('monthly_cents')->default(75000);
            $table->string('payment_link_id')->nullable();
            $table->enum('payment_status', ['pending','paid','failed','refunded'])->default('pending');
            $table->enum('provision_status', ['not_started','website_pending','website_done','listing_pending','listing_done','whatsapp_pending','whatsapp_done','completed','failed'])->default('not_started');
            $table->string('website_url')->nullable();
            $table->string('listing_url')->nullable();
            $table->string('shop_app_url')->nullable();
            $table->foreignId('business_id')->nullable()->constrained()->nullOnDelete();
            $table->dateTime('paid_at')->nullable();
            $table->dateTime('provisioned_at')->nullable();
            $table->text('provision_error')->nullable();
            $table->timestamps();
            $table->index(['payment_status','provision_status']);
            $table->index(['owner_phone']);
        });
    }
    public function down(): void { Schema::dropIfExists('business_in_a_box_orders'); }
};
