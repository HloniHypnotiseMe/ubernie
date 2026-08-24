<?php

return [
    'remotepay' => [
        'base_url' => env('REMOTEPAY_API_BASE_URL'),
        'timeout' => env('REMOTEPAY_API_TIMEOUT', 15),
    ],
];
