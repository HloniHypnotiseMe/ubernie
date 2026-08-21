<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('enterprise_audits', function (Blueprint $table) {
            $table->id();
            $table->foreignId('business_id')->constrained()->cascadeOnDelete();
            $table->enum('status', ['pending_audit', 'audited', 'quoted', 'closed'])->default('pending_audit');
            $table->text('audit_notes')->nullable();
            $table->decimal('proposed_monthly_price', 12, 2)->nullable();
            $table->boolean('requires_senior_sales_agent')->default(true);
            $table->foreignId('assigned_sales_agent_id')->nullable()->constrained('users');
            $table->timestamps();
        });
    }
};