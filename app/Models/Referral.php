<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Referral extends Model
{
    protected $fillable = ['affiliate_id', 'referred_business_id', 'referred_user_id', 'total_commission_earned'];
}