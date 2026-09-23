<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\RiskLiaisonController;

Route::middleware('api')->post('/risk/liaison', [RiskLiaisonController::class, 'store']);
