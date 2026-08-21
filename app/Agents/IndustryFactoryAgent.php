<?php

namespace App\Agents;

use App\Models\SearchDemand;

class IndustryFactoryAgent
{
    public function createIndustry(SearchDemand $demand): array
    {
        if ($demand->industry_created) {
            return ['status' => 'already_exists'];
        }

        // Auto-generate industry assets
        $industrySlug = str_replace(' ', '-', strtolower($demand->search_term));

        $assets = [
            'industry_page' => "industries/{$industrySlug}",
            'seo_title' => "Best " . ucwords($demand->search_term) . " in South Africa",
            'landing_page' => "https://{$industrySlug}.ubernie.co.za",
            'waitlist_enabled' => true,
            'lead_capture' => ['Get Quotes', 'Join Waitlist', 'List Your Business'],
        ];

        $demand->update([
            'industry_created' => true,
            'subdomain_created' => true,
        ]);

        return [
            'status' => 'created',
            'assets' => $assets,
            'subdomain' => "{$industrySlug}.ubernie.co.za",
        ];
    }
}