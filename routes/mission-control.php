<?php

use App\Agents\MasterOrchestratorAgent;
use App\Models\Business;
use Illuminate\Support\Facades\Route;

Route::post('/internal/mission-control/ubernie/business/{business}', function (Business $business) {
    $expected = (string) config('services.mission_control.token', '');
    $provided = (string) request()->header('X-C6-Mission-Token', '');

    if ($expected === '' || $provided === '' || !hash_equals($expected, $provided)) {
        abort(401, 'Mission Control authentication required.');
    }

    return response()->json([
        'status' => 'EXECUTED',
        'product' => 'Ubernie',
        'agent' => 'ubernie_master_orchestrator',
        'action_type' => 'orchestrate_business',
        'business_id' => $business->id,
        'result' => (new MasterOrchestratorAgent())->onboardBusiness(
            $business,
            request()->only(['industry'])
        ),
    ]);
});
