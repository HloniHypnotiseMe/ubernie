<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;

class WinEventService
{
    public function emit(array $event): void
    {
        $url = env('C6_WIN_ENGINE_URL');
        if (!$url) {
            return;
        }

        $payload = array_merge([
            'project' => 'Ubernie',
            'actor' => 'ubernie',
            'tier' => 'EXECUTION',
        ], $event);

        try {
            $request = Http::timeout(3);
            if ($token = env('C6_WIN_ENGINE_TOKEN')) {
                $request = $request->withHeaders(['X-C6-Win-Token' => $token]);
            }
            $request->post($url, $payload);
        } catch (\Throwable $e) {
            // Win tracking is observability and must never block directory operations.
            report($e);
        }
    }
}
