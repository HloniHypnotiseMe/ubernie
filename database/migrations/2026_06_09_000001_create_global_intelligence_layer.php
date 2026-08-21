<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->uuid('global_uuid')->unique()->after('id')->nullable();
            $table->enum('lifecycle_stage', ['lead', 'onboarded', 'active', 'churned'])->default('lead');
            $table->json('system_access')->nullable();
        });

        Schema::table('businesses', function (Blueprint $table) {
            $table->uuid('global_uuid')->unique()->after('id')->nullable();
            $table->string('source_system')->default('ubernie');
            $table->foreignId('referred_by_affiliate_id')->nullable()->constrained('affiliates');
            $table->tinyInteger('maturity_level')->default(0);
        });

        Schema::create('referral_sources', function (Blueprint $table) {
            $table->id();
            $table->foreignId('affiliate_id')->constrained()->cascadeOnDelete();
            $table->foreignId('business_id')->constrained()->cascadeOnDelete();
            $table->string('source_channel')->nullable();
            $table->timestamps();
        });

        Schema::create('system_events', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->nullable()->constrained()->cascadeOnDelete();
            $table->foreignId('business_id')->nullable()->constrained()->cascadeOnDelete();
            $table->string('event_type');
            $table->string('source_system');
            $table->json('payload')->nullable();
            $table->timestamps();
        });
    }
};