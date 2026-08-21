@extends('layouts.app')

@section('content')
<div class="max-w-3xl mx-auto py-12 px-4" x-data="{ showBuild: false }">
    <div class="bg-white rounded-2xl shadow p-8">
        <h1 class="text-3xl font-bold mb-2">Ubernie Business Intelligence Agent</h1>
        <p class="text-gray-600 mb-6">"We didn’t just list your business — we upgraded it into a system."</p>

        <div class="bg-green-50 border border-green-200 rounded-xl p-6 mb-8">
            <div class="flex items-center gap-4">
                <div class="text-4xl">{{ $diagnosis['level'] }}</div>
                <div>
                    <div class="font-semibold text-xl">{{ $diagnosis['diagnosis'] }}</div>
                    <div class="text-sm text-gray-600 mt-1">Recommended: {{ $diagnosis['recommended_tier'] }} Tier</div>
                </div>
            </div>
        </div>

        <h3 class="font-semibold mb-3">Missing Elements Detected</h3>
        <ul class="list-disc pl-6 mb-8 text-gray-700">
            @foreach($diagnosis['missing_elements'] as $gap)
                <li>{{ $gap }}</li>
            @endforeach
        </ul>

        <button @click="showBuild = true" 
                class="w-full bg-green-600 hover:bg-green-700 text-white py-4 rounded-xl font-semibold text-lg transition">
            Auto-Build My Business Now →
        </button>
    </div>

    <div x-show="showBuild" x-transition class="mt-8">
        <form action="{{ route('agent.build', $business ?? 1) }}" method="POST">
            @csrf
            <button type="submit" 
                    class="w-full bg-emerald-600 text-white py-4 rounded-xl font-semibold">
                Confirm &amp; Generate Full Business System
            </button>
        </form>
    </div>
</div>
@endsection