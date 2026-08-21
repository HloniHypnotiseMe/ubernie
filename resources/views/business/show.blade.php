@extends('layouts.app')

@section('content')
<div class="max-w-5xl mx-auto px-6 py-12">
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Business Profile -->
        <div class="lg:col-span-2">
            <h1 class="text-4xl font-bold mb-2">{{ $business->name }}</h1>
            <div class="flex items-center gap-3 mb-6">
                <span class="px-4 py-1 rounded-full text-sm font-medium bg-green-100 text-green-700">{{ $business->category->name ?? 'Business' }}</span>
                <span class="text-sm text-gray-500">{{ $business->city->name ?? 'South Africa' }}</span>
            </div>
            
            <div class="prose max-w-none">
                {!! $business->description !!}
            </div>
        </div>

        <!-- Agent Sidebar -->
        <div class="lg:col-span-1">
            <div class="sticky top-8 bg-white border border-gray-200 rounded-3xl p-8">
                <div class="text-center mb-6">
                    <div class="text-4xl mb-3">🤖</div>
                    <div class="font-semibold text-xl">Ubernie Intelligence Agent</div>
                </div>
                
                <a href="{{ route('agent.chat') }}" 
                   class="block w-full text-center bg-green-600 hover:bg-green-700 text-white py-4 rounded-2xl font-semibold mb-4 transition">
                    Upgrade This Business
                </a>
                
                <div class="text-xs text-center text-gray-500">
                    Get diagnosed • Auto-build profile • Get tier pricing + ecosystem recommendations
                </div>
            </div>
        </div>
    </div>
</div>
@endsection