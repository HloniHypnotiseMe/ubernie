@extends('layouts.app')

@section('content')
<div class="max-w-7xl mx-auto px-6 py-16">
    <!-- Hero -->
    <div class="text-center mb-16">
        <h1 class="text-6xl font-bold tracking-tight mb-4">South Africa’s Business Intelligence Platform</h1>
        <p class="text-2xl text-gray-600 max-w-2xl mx-auto">We don’t just list businesses — we upgrade them into complete, monetizable systems.</p>
        
        <div class="mt-10 flex justify-center gap-4">
            <a href="{{ route('agent.chat') }}" 
               class="inline-flex items-center gap-3 bg-green-600 hover:bg-green-700 text-white px-10 py-5 rounded-2xl text-xl font-semibold shadow-lg transition">
                Talk to the Ubernie Agent →
            </a>
            <a href="#directory" class="inline-flex items-center gap-3 border border-gray-300 hover:bg-gray-50 px-10 py-5 rounded-2xl text-xl font-semibold transition">
                Browse Directory
            </a>
        </div>
    </div>

    <!-- Agent Teaser -->
    <div class="bg-gradient-to-br from-green-50 to-white border border-green-100 rounded-3xl p-12 text-center mb-20">
        <div class="max-w-md mx-auto">
            <div class="text-green-600 text-5xl mb-4">🤖</div>
            <h2 class="text-3xl font-bold mb-3">Meet Your Business Upgrade Engine</h2>
            <p class="text-gray-600 mb-8">Our AI agent diagnoses your business, builds your profile, recommends the perfect tier, and connects you to C6 &amp; RemotePay — all in one conversation.</p>
            <a href="{{ route('agent.chat') }}" class="inline-block bg-white border border-green-600 text-green-600 hover:bg-green-600 hover:text-white px-8 py-3 rounded-2xl font-semibold transition">Start Free Diagnosis</a>
        </div>
    </div>
</div>
@endsection