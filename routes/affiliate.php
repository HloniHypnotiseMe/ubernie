<?php

use App\Http\Controllers\AffiliateController;
use Illuminate\Support\Facades\Route;

Route::middleware('auth')->group(function () {
    Route::get('/affiliate/dashboard', [AffiliateController::class, 'dashboard'])->name('affiliate.dashboard');
    Route::get('/affiliate/terms', [AffiliateController::class, 'terms'])->name('affiliate.terms');
    Route::get('/affiliate/faq', [AffiliateController::class, 'faq'])->name('affiliate.faq');
});