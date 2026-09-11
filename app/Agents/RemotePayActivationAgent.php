<?php

namespace App\Agents;

use App\Models\Business;
use App\Services\RemotePayClient;
use Illuminate\Support\Str;

class RemotePayActivationAgent
{
    public function shouldRecommendRemotePay(Business $business): bool
    {
        // Trigger if business has any payment-related signals
        return $business->has_payments ||
               $business->has_invoicing ||
               $business->has_recurring_customers ||
               $business->sells_online;
    }

    public function createRemotePayLead(Business $business): array
    {
        if ($this->shouldRecommendRemotePay($business)) {
            return [
                'business_id' => $business->id,
                'action' => 'create_remote_pay_lead',
                'message' => 'RemotePay recommended based on business profile.',
            ];
        }

        return ['action' => 'no_recommendation'];
    }

    public function createPaymentLink(
        Business $business,
        int $amountMinor,
        string $description,
        string $idempotencyKey,
        array $metadata = []
    ): array {
        return app(RemotePayClient::class)->createPaymentLink([
            'merchant_id' => (string) config('services.remotepay.merchant_id', 'ubernie'),
            'brand_id' => (string) config('services.remotepay.brand_id', 'ubernie'),
            'source_system' => 'ubernie',
            'customer_reference' => 'business:' . $business->id,
            'description' => $description,
            'amount_minor' => $amountMinor,
            'currency' => 'ZAR',
            'idempotency_key' => $idempotencyKey,
            'metadata' => array_merge([
                'business_id' => (string) $business->id,
                'business_name' => $business->name,
                'source' => 'ubernie',
            ], $metadata),
        ]);
    }
}
