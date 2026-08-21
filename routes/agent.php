<?php

use App\Http\Controllers\AgentController;
use Illuminate\Support\Facades\Route;

Route::middleware('auth')->group(function () {
    Route::get('/agent/chat', fn() => view('agent.chat'))->name('agent.chat');
    Route::post('/agent/intake', [AgentController::class, 'intake'])->name('agent.intake');
    Route::post('/agent/build/{business}', [AgentController::class, 'buildBusiness'])->name('agent.build');
    Route::get('/agent/recommend/{business}', [AgentController::class, 'recommendEcosystem']);
});