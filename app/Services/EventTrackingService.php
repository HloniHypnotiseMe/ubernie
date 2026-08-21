<?php

namespace App\Services;

use App\Models\SystemEvent;

class EventTrackingService
{
    public function track(string $eventType, $business = null, $user = null, array $payload = [], string $source = 'ubernie'): void
    {
        SystemEvent::create([
            'user_id'       => $user?->id,
            'business_id'   => $business?->id,
            'event_type'    => $eventType,
            'source_system' => $source,
            'payload'       => $payload,
        ]);
    }
}