<?php

namespace App\Agents;

use App\Models\Business;
use App\Models\SearchDemand;
use App\Agents\DiscoveryAgent;
use App\Agents\IndustryFactoryAgent;
use App\Agents\BusinessInABoxAgent;
use App\Agents\RemotePayActivationAgent;
use App\Agents\SubdomainFactoryAgent;

class MasterOrchestratorAgent
{
    protected DiscoveryAgent $discovery;
    protected IndustryFactoryAgent $industryFactory;
    protected BusinessInABoxAgent $businessInABox;
    protected RemotePayActivationAgent $remotePay;
    protected SubdomainFactoryAgent $subdomainFactory;
    protected \App\Services\WinEventService $winEvents;

    public function __construct()
    {
        $this->discovery = new DiscoveryAgent();
        $this->industryFactory = new IndustryFactoryAgent();
        $this->businessInABox = new BusinessInABoxAgent();
        $this->remotePay = new RemotePayActivationAgent();
        $this->subdomainFactory = new SubdomainFactoryAgent();
        $this->winEvents = new \App\Services\WinEventService();
    }

    public function handleSearch(string $searchTerm): array
    {
        $this->discovery->recordSearch($searchTerm);

        $demand = SearchDemand::where('search_term', strtolower($searchTerm))->first();

        if ($demand && $demand->search_count >= 25 && !$demand->industry_created) {
            return $this->industryFactory->createIndustry($demand);
        }

        return ['status' => 'monitored'];
    }

    public function onboardBusiness(Business $business, array $data = []): array
    {
        $results = [];

        // Business In A Box
        $results['business_in_a_box'] = $this->businessInABox->auditBusiness($business);

        // RemotePay Activation
        if ($this->remotePay->shouldRecommendRemotePay($business)) {
            $results['remote_pay'] = $this->remotePay->createRemotePayLead($business);
        }

        // Subdomain suggestion (if industry exists)
        if (!empty($data['industry'])) {
            $results['subdomain'] = $this->subdomainFactory->generateSubdomain($data['industry']);
        }

        $this->winEvents->emit([
            'objective' => 'Activate a business inside the Ubernie growth system',
            'minimum_winnable_action' => 'Complete directory diagnosis and routing for one business',
            'proof_required' => 'Orchestration result containing a business diagnosis',
            'project' => 'Ubernie',
            'actor' => 'ubernie_master_orchestrator',
            'tier' => 'MARKET',
            'evidence' => [
                'event' => 'business_orchestration_completed',
                'business_id' => $business->id,
                'result_keys' => array_keys($results),
            ],
            'capability_unlocked' => 'Business discovery and cross-system routing',
            'next_win' => 'Activate the selected business system and capture external evidence',
        ]);

        return $results;
    }

    public function runFullOrchestration(Business $business = null, string $searchTerm = null): array
    {
        $output = [];

        if ($searchTerm) {
            $output['search'] = $this->handleSearch($searchTerm);
        }

        if ($business) {
            $output['business'] = $this->onboardBusiness($business);
        }

        return $output;
    }
}