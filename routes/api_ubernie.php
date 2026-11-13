<?php
use Illuminate\Support\Facades\Route;
// Ubernie Super App API - Shop + Driver + SmartDrinker + Customer
// Auth: Sanctum + WhatsApp OTP (to be wired)
Route::prefix('v1/ubernie')->group(function () {
    // Public - Search + Categories + Deals
    Route::get('/categories', fn() => response()->json(['message' => 'List categories']));
    Route::get('/nearby', fn() => response()->json(['message' => 'Geo matching - nearest by ETA + rating']));
    Route::get('/deals', fn() => response()->json(['message' => 'Thursday Deals + Vouchers']));
    Route::get('/drinking-well', fn() => response()->json(['message' => 'Drinking Well + Smart Drinker banner after 18:00']));
    // Leads - Customer -> Shop
    Route::post('/leads', fn() => response()->json(['message' => 'Create lead - inquiry state']));
    Route::get('/leads/{id}', fn($id) => response()->json(['message' => "Lead $id status"]));
    // Shop App - Requires Auth
    Route::middleware('auth:sanctum')->group(function () {
        Route::get('/shop/leads', fn() => response()->json(['message' => 'Shop leads']));
        Route::post('/shop/leads/{id}/reply', fn($id) => response()->json(['message' => "Reply to lead $id"]));
        Route::post('/shop/deals', fn() => response()->json(['message' => 'Post Thursday Deal']));
        Route::post('/shop/mark-paid', fn() => response()->json(['message' => 'Mark paid via RemotePay']));
        // Business in a Box - One Checkout = One Box
    Route::post('/business-in-a-box/checkout', fn() => response()->json(['message' => 'Create Business in a Box order - R9500 + R750/mo - Returns RemotePay payment-link']));
    Route::post('/business-in-a-box/webhook', fn() => response()->json(['message' => 'RemotePay webhook - payment.paid -> auto-provision website + listing + whatsapp + CRM']));
    Route::get('/business-in-a-box/{id}', fn($id) => response()->json(['message' => "Box $id - payment + provision status"]));
});
    // Driver App - Requires Auth
    Route::middleware('auth:sanctum')->group(function () {
        Route::post('/driver/online', fn() => response()->json(['message' => 'Driver online']));
        Route::post('/driver/offline', fn() => response()->json(['message' => 'Driver offline']));
        Route::get('/driver/demand', fn() => response()->json(['message' => 'Demand zones + multiplier']));
        Route::post('/driver/accept-delivery', fn() => response()->json(['message' => 'Accept delivery']));
    });
    // Smart Drinker - Requires Auth for Driver, Public for Booking
    Route::post('/smart-drinker/book', fn() => response()->json(['message' => 'Book Take Me Home - upfront price']));
    Route::post('/smart-drinker/accept', fn() => response()->json(['message' => 'Driver accept Smart Drinker']));
    Route::post('/smart-drinker/otp-verify', fn() => response()->json(['message' => 'OTP verify trip start']));
    Route::get('/smart-drinker/track/{token}', fn($t) => response()->json(['message' => "Track trip $t"]));
    // Delivery Waitlists
    Route::post('/delivery/waitlist-shop', fn() => response()->json(['message' => 'Join shop waitlist']));
    Route::post('/delivery/waitlist-driver', fn() => response()->json(['message' => 'Join driver waitlist']));
    Route::get('/delivery/zones', fn() => response()->json(['message' => 'Demand zones progress 3/10 shops']));
});
