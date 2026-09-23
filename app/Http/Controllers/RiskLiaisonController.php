<?php

namespace App\Http\Controllers;

use App\Services\RiskLiaisonService;
use Illuminate\Http\Request;

class RiskLiaisonController extends Controller
{
    public function store(Request $request, RiskLiaisonService $liaison)
    {
        $data = $request->validate([
            'severity' => ['required', 'in:LOW,MEDIUM,HIGH,CRITICAL'],
            'signal' => ['required', 'string', 'max:500'],
            'context' => ['nullable', 'array'],
        ]);

        return response()->json(
            $liaison->emit($data['severity'], $data['signal'], $data['context'] ?? [])
        );
    }
}
