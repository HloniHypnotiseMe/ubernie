<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class RiskLiaisonTest extends TestCase
{
    use RefreshDatabase;

    public function test_risk_liaison_route_exists(): void
    {
        $response = $this->postJson('/api/risk/liaison', [
            'severity' => 'HIGH',
            'signal' => 'test risk signal',
            'context' => ['tenant_id' => 'test'],
        ]);

        $this->assertNotSame(404, $response->status());
    }
}
