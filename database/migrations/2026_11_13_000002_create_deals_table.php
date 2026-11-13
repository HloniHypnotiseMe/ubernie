<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
return new class extends Migration {
    public function up(): void {
        Schema::create('deals', function (Blueprint $table) {
            $table->id();
            $table->foreignId('business_id')->constrained()->cascadeOnDelete();
            $table->foreignId('category_id')->nullable()->constrained()->nullOnDelete();
            $table->string('title');
            $table->string('slug')->unique();
            $table->text('description')->nullable();
            $table->string('voucher_code')->nullable()->unique();
            $table->decimal('original_price', 10, 2)->nullable();
            $table->decimal('deal_price', 10, 2)->nullable();
            $table->integer('discount_percent')->nullable();
            $table->enum('deal_type', ['thursday_deal','voucher','daily_deal','clearance'])->default('thursday_deal');
            $table->dateTime('starts_at');
            $table->dateTime('ends_at');
            $table->integer('max_redemptions')->default(100);
            $table->integer('redemptions_count')->default(0);
            $table->enum('status', ['draft','pending','approved','live','expired','rejected'])->default('pending');
            $table->boolean('featured')->default(false);
            $table->timestamps();
            $table->index(['deal_type','status','starts_at','ends_at']);
            $table->index(['business_id','status']);
        });
    }
    public function down(): void { Schema::dropIfExists('deals'); }
};
