<?php

namespace App\Services;

use App\Models\Business;
use App\Services\UbernieAgentService;
use App\Services\EventTrackingService;
use App\Services\AffiliatePayoutService;

class MasterOrchestratorAgent
{
    public function processBusinessIntake(Business $business, array $data)
    {
        // 1. Run Ubernie Agent
        $uberAgent = app(UbernieAgentService::class);
        $diagnosis = $uberAgent->diagnoseBusiness($data);
        $business = $uberAgent->autoBuildBusiness($business, $data);

        // 2. Track the event
        app(EventTrackingService::class)->track('business_intake', $business, null, $diagnosis);

        // 3. Handle affiliate payout logic
        if ($business->referred_by_affiliate_id) {
            $payoutService = app(AffiliatePayoutService::class);
            $referral = $business->referral;
            $payoutService->markCommissionPayable($referral);
        }

        return $diagnosis;
    }
}