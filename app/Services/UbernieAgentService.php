<?php

namespace App\Services;

use App\Models\Business;
use App\Models\BusinessLevel;
use App\Models\Recommendation;
use App\Models\BusinessTier;
use Illuminate\Support\Str;

class UbernieAgentService
{
    public function diagnoseBusiness(array $data): array
    {
        $level = $this->determineLevel($data);
        
        return [
            'level' => $level,
            'diagnosis' => $this->getDiagnosisText($level),
            'missing_elements' => $this->identifyGaps($data, $level),
            'recommended_tier' => $this->recommendTier($level),
        ];
    }

    public function autoBuildBusiness(Business $business, array $data): Business
    {
        // Auto-generate SEO description, category if missing, structured fields
        if (!$business->description) {
            $business->description = $this->generateSEODescription($data);
        }
        
        if (!$business->slug) {
            $business->slug = Str::slug($business->name);
        }

        // Create category if needed
        // ... (logic for auto category creation)

        $business->save();
        
        // Log recommendation
        Recommendation::create([
            'business_id' => $business->id,
            'type' => 'auto_build',
            'message' => 'Business upgraded with AI-generated profile, SEO, and structure.',
        ]);

        return $business;
    }

    public function generateRecommendations(Business $business): array
    {
        $recs = [
            [
                'type' => 'visibility',
                'title' => 'Upgrade to Growth Tier',
                'description' => 'Get featured placement and lead boost on Ubernie.',
                'action' => 'Route to Ubernie Growth Tier',
            ],
            [
                'type' => 'payments',
                'title' => 'Enable Payments',
                'description' => 'Connect RemotePay for seamless transactions.',
                'action' => 'Route to RemotePay',
            ],
            [
                'type' => 'intelligence',
                'title' => 'Run C6 Business Audit',
                'description' => 'Get deep business intelligence and optimization.',
                'action' => 'Route to C6 Group',
            ],
        ];

        // Enterprise special rule
        if ($business->tier === 'enterprise') {
            $recs[] = [
                'type' => 'enterprise',
                'title' => 'Enterprise Premium Pricing',
                'description' => 'Custom audit-based pricing. Senior Sales Agent will contact you.',
                'action' => 'Request Enterprise Audit',
            ];
        }

        return $recs;
    }

    public function generateBusinessInABox(int $level): array
    {
        $tiers = [
            0 => 'Starter Business System',
            1 => 'Growth Business System',
            2 => 'Dominance Business System',
            3 => 'Enterprise Business System',
        ];

        return [
            'bundle' => $tiers[$level] ?? 'Starter Business System',
            'includes' => [
                'Structured profile + SEO',
                'Lead capture + WhatsApp funnel',
                'Tier upgrade path',
                'Cross-system routing (C6 + RemotePay)',
            ],
        ];
    }

    private function determineLevel(array $data): int
    {
        $score = 0;
        if (!empty($data['website'])) $score++;
        if (!empty($data['branding'])) $score++;
        if (!empty($data['customers'])) $score++;
        if (!empty($data['scalable_system'])) $score++;

        return min($score, 3);
    }

    private function getDiagnosisText(int $level): string
    {
        return match($level) {
            0 => '🟢 Level 0 — No Digital Presence',
            1 => '🔵 Level 1 — Basic Presence',
            2 => '🟣 Level 2 — Active Business',
            3 => '🔴 Level 3 — Structured Business',
        };
    }

    private function identifyGaps(array $data, int $level): array
    {
        // Logic to detect missing website, payments, branding, etc.
        return ['website', 'payments', 'structured_profile'];
    }

    private function recommendTier(int $level): string
    {
        return match($level) {
            0 => 'Starter',
            1 => 'Growth',
            2 => 'Power',
            3 => 'Enterprise',
        };
    }

    private function generateSEODescription(array $data): string
    {
        return "Discover {$data['name']} — premium {$data['category']} in {$data['location']}. Quality service with fast response.";
    }

    public function createAffiliateReferral(int $affiliateId, Business $business, int $userId): void
    {
        Referral::create([
            'affiliate_id' => $affiliateId,
            'referred_business_id' => $business->id,
            'referred_user_id' => $userId,
            'total_commission_earned' => 0, // Will be calculated on tier upgrade
        ]);
    }
}