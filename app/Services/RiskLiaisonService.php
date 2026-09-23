<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;

class RiskLiaisonService
{
    public function emit(string $severity, string $signal, array $context = []): array
    {
        $base = rtrim((string) config('services.c6_saas_core.url'), '/');
        if ($base === '') {
            return ['status' => 'GAP', 'reason' => 'C6 SaaS Core URL not configured'];
        }

        try {
            $response = Http::timeout(5)->post($base.'/api/v1/audit', [
                'tenant_id' => (string) ($context['tenant_id'] ?? 'ubernie'),
                'actor_id' => (string) ($context['actor_id'] ?? 'ubernie-risk-liaison'),
                'action' => 'risk.signal',
                'target' => $signal,
                'decision' => 'ESCALATE',
                'policy_id' => 'brand-risk-liaison-v1',
                'evidence' => [
                    'severity' => $severity,
                    'context' => $context,
                ],
            ]);

            return [
                'status' => $response->successful() ? 'WORKS' : 'GAP',
                'http_status' => $response->status(),
            ];
        } catch (\Throwable $e) {
            return ['status' => 'GAP', 'reason' => $e->getMessage()];
        }
    }
}
