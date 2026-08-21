<?php

namespace App\Services;

use App\Models\Referral;

class AffiliatePayoutService
{
    public function calculateMonthlyCommission(Referral $referral): float
    {
        $monthlyRevenue = $referral->business->current_tier_price ?? 0;
        return round($monthlyRevenue * 0.25, 2);
    }

    public function markCommissionPayable(Referral $referral): void
    {
        if ($referral->created_at->diffInDays(now()) >= 30 && !$referral->fraud_flagged) {
            $referral->update(['status' => 'payable']);
        }
    }

    public function detectFraud(Referral $referral): bool
    {
        return $referral->business->user_id === $referral->referred_user_id;
    }
}