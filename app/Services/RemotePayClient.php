<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use RuntimeException;

class RemotePayClient
{
    public function createPaymentLink(array $payload): array
    {
        $baseUrl = rtrim((string) config('services.remotepay.base_url'), '/');

        if ($baseUrl === '') {
            throw new RuntimeException('REMOTEPAY_API_BASE_URL is not configured.');
        }

        return Http::acceptJson()
            ->asJson()
            ->timeout((int) config('services.remotepay.timeout', 15))
            ->post($baseUrl . '/api/v1/payment-links', $payload)
            ->throw()
            ->json();
    }
}
