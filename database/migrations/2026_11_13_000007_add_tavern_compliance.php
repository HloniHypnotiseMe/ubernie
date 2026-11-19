<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
return new class extends Migration {
    public function up(): void {
        Schema::table('businesses', function (Blueprint $table) {
            $table->string('liquor_licence_number')->nullable();
            $table->date('liquor_licence_expiry')->nullable();
            $table->enum('rtp_status', ['none','silver','gold','platinum'])->default('none');
            $table->boolean('id_check_at_door')->default(false);
            $table->boolean('no_under18_sign')->default(false);
            $table->boolean('smart_drinker_offered')->default(false);
            $table->boolean('sells_zero_alcohol')->default(false);
        });
    }
    public function down(): void {
        Schema::table('businesses', function (Blueprint $table) {
            $table->dropColumn(['liquor_licence_number','liquor_licence_expiry','rtp_status','id_check_at_door','no_under18_sign','smart_drinker_offered','sells_zero_alcohol']);
        });
    }
};
