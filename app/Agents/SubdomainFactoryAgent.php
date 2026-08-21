<?php

namespace App\Agents;

class SubdomainFactoryAgent
{
    public function generateSubdomain(string $industry): string
    {
        $slug = str_replace(' ', '-', strtolower($industry));
        return "{$slug}.ubernie.co.za";
    }
}