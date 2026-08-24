<?php

return [
    'remotepay' => [
        'base_url' => env('REMOTEPAY_API_BASE_URL'),
        'timeout' => env('REMOTEPAY_API_TIMEOUT', 15),
        'merchant_id' => env('REMOTEPAY_MERCHANT_ID', 'ubernie'),
        'brand_id' => env('REMOTEPAY_BRAND_ID', 'ubernie'),
    ],
];
