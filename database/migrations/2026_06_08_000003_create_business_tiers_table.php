<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('business_tiers', function (Blueprint $table) {
            $table->id();
            $table->foreignId('business_id')->constrained()->cascadeOnDelete();
            $table->enum('tier', ['starter', 'growth', 'power', 'enterprise'])->default('starter');
            $table->decimal('monthly_price', 10, 2)->nullable();
            $table->boolean('requires_senior_sales')->default(false);
            $table->boolean('audit_required')->default(false);
            $table->text('pricing_notes')->nullable();
            $table->timestamps();
        });
    }
};