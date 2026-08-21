<?php

use Illuminate\Support\Facades\Route;

// Affiliate routes
require __DIR__.'/affiliate.php';
require __DIR__.'/agent.php';

Route::get('/', function () {
    return view('home');
})->name('home');
