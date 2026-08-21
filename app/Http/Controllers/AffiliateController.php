<?php

namespace App\Http\Controllers;

use App\Models\Affiliate;
use App\Models\Referral;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class AffiliateController extends Controller
{
    public function dashboard()
    {
        $user = Auth::user();
        $affiliate = $user->affiliate ?? Affiliate::create([
            'user_id' => $user->id,
            'referral_code' => strtoupper(substr(md5($user->id), 0, 8)),
        ]);

        $referrals = Referral::where('affiliate_id', $affiliate->id)
            ->with('business')
            ->latest()
            ->take(20)
            ->get();

        $stats = [
            'total_referrals'   => $referrals->count(),
            'active_customers'  => $referrals->where('status', 'active')->count(),
            'monthly_earnings'  => $referrals->sum('monthly_commission'),
            'lifetime_earnings' => $referrals->sum('total_earned'),
        ];

        return view('affiliate.dashboard', compact('affiliate', 'referrals', 'stats'));
    }

    public function terms()
    {
        return view('affiliate.terms');
    }

    public function faq()
    {
        return view('affiliate.faq');
    }
}