<?php

namespace App\Http\Controllers;

use App\Services\UbernieAgentService;
use App\Models\Business;
use Illuminate\Http\Request;

class AgentController extends Controller
{
    protected $agent;

    public function __construct(UbernieAgentService $agent)
    {
        $this->agent = $agent;
    }

    public function intake(Request $request)
    {
        $data = $request->validate([
            'name' => 'required',
            'location' => 'required',
            'category' => 'required',
            'offerings' => 'nullable',
        ]);

        $diagnosis = $this->agent->diagnoseBusiness($data);
        
        return view('agent.diagnosis', compact('diagnosis', 'data'));
    }

    public function buildBusiness(Request $request, Business $business)
    {
        $business = $this->agent->autoBuildBusiness($business, $request->all());
        
        $recommendations = $this->agent->generateRecommendations($business);
        $bundle = $this->agent->generateBusinessInABox($diagnosis['level'] ?? 0);

        return view('agent.upgraded', [
            'business' => $business,
            'recommendations' => $recommendations,
            'bundle' => $bundle,
        ]);
    }

    public function recommendEcosystem(Business $business)
    {
        $recs = $this->agent->generateRecommendations($business);
        return response()->json($recs);
    }
}