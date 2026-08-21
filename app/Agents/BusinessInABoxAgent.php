<?php

namespace App\Agents;

use App\Models\Business;

class BusinessInABoxAgent
{
    public function auditBusiness(Business $business): array
    {
        $gaps = [];

        // Simple audit simulation
        if (!$business->website) $gaps[] = 'website';
        if (!$business->has_payments) $gaps[] = 'payments';
        if (!$business->has_crm) $gaps[] = 'crm';
        if (!$business->has_bookings) $gaps[] = 'bookings';
        if (!$business->has_whatsapp) $gaps[] = 'whatsapp';

        return [
            'business_id' => $business->id,
            'gaps_detected' => $gaps,
            'recommended_bundle' => $this->recommendBundle($gaps),
        ];
    }

    private function recommendBundle(array $gaps): array
    {
        $count = count($gaps);

        if ($count <= 2) {
            return [
                'name' => 'Starter Bundle',
                'price' => 99,
                'includes' => ['Website', 'Directory Listing', 'WhatsApp Lead Capture'],
            ];
        } elseif ($count <= 4) {
            return [
                'name' => 'Growth Bundle',
                'price' => 299,
                'includes' => ['Website', 'RemotePay', 'CRM', 'Bookings'],
            ];
        } else {
            return [
                'name' => 'Scale Bundle',
                'price' => 999,
                'includes' => ['Website', 'RemotePay', 'CRM', 'Marketing Automation', 'Analytics'],
            ];
        }
    }
}