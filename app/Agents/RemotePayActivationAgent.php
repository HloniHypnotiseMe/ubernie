<?php

namespace App\Agents;

use App\Models\Business;

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
}