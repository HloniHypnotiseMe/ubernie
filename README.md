# Ubernie - South African Business Discovery & Marketplace Platform

**Production-Ready Laravel 12 Application**

- Domain: www.ubernie.co.za
- Tech Stack: Laravel 12, PHP 8.4, MySQL 8, TailwindCSS, Alpine.js, Meilisearch, Leaflet (OSM)
- Mobile-first | SEO-optimized | VPS-ready | Green brand identity

This repository contains the complete production-ready codebase for Phase 1 of Ubernie.

## Project Structure

```
ubernie/
├── app/
│   ├── Http/
│   │   ├── Controllers/
│   │   │   ├── Admin/
│   │   │   ├── Api/
│   │   │   ├── Auth/
│   │   │   ├── BusinessController.php
│   │   │   ├── MarketplaceController.php
│   │   │   ├── DriverController.php
│   │   │   ├── MerchantController.php
│   │   │   └── HomeController.php
│   ├── Models/
│   │   ├── User.php
│   │   ├── Business.php
│   │   ├── Category.php
│   │   ├── Listing.php
│   │   ├── Driver.php
│   │   ├── Merchant.php
│   │   ├── City.php
│   │   ├── SearchLog.php
│   │   └── ...
│   ├── Services/
│   │   ├── SearchService.php
│   │   ├── GeolocationService.php
│   │   └── AnalyticsService.php
├── database/
│   ├── migrations/
│   ├── seeders/
│   └── factories/
├── resources/
│   ├── views/
│   │   ├── layouts/
│   │   ├── business/
│   │   ├── marketplace/
│   │   ├── driver/
│   │   ├── merchant/
│   │   ├── admin/
│   │   └── components/
│   ├── css/
│   └── js/
├── routes/
│   ├── web.php
│   ├── api.php
│   └── admin.php
├── config/
│   ├── meilisearch.php
│   └── ...
├── public/
├── .env.example
├── composer.json
├── package.json
├── README.md (this file)
├── INSTALL.md
├── DEPLOY.md
└── SECURITY.md
```

## Database Schema (High-Level)

- **users**: id, name, email, password, phone, role (user, driver, merchant, admin), city_id, verified_at, ...
- **businesses**: id, user_id, name, slug, category_id, description, address, lat, lng, phone, email, website, logo, status (pending, approved, rejected), featured, ...
- **categories**: id, name, slug, parent_id, icon
- **listings**: id, user_id, business_id, title, description, price, images (json), status, ...
- **drivers**: id, user_id, license_number, vehicle_type, city_id, status (waitlist, approved), ...
- **merchants**: id, business_id, delivery_interest (bool), preferred_cities (json), ...
- **cities**: id, name, province, slug, lat, lng
- **search_logs**: id, query, user_id, results_count, city_id, created_at
- **analytics_events**: ...

Full migrations provided in `database/migrations/`

## Key Features Implemented in Phase 1 + Agent Layer

1. **Business Directory** - Search with Meilisearch, categories, map with Leaflet, profiles
2. **Marketplace** - User listings with moderation
3. **Driver & Merchant Waitlists** - Registration forms with city assignment
4. **Admin Dashboard** - Full management + analytics
5. **SEO** - Meta tags, sitemaps, structured data
6. **Mobile-first** - Tailwind + Alpine.js
7. **Ubernie Business Intelligence Agent** - Full 9-step intelligent flow:
   - Auto diagnosis (Levels 0-3)
   - Auto business building
   - Cross-system routing (C6 + RemotePay)
   - Monetization tiers & Business-in-a-Box bundles
   - Viral loop + recommendations engine
8. **Affiliate Program** - 25% lifetime recurring commissions with dashboard, leads tracker, welcome flows, and Q&A

### Business Model & Monetization Logic (Updated)
- **Platform Revenue**: Monthly recurring subscriptions (Starter R299 → Enterprise custom R8k–R25k+)
- **Affiliate Revenue Share**: 25% lifetime commission on all referred customers
- **Enterprise Rule**: Audit-first + senior sales agent (no low fixed pricing)
- **Agent-Driven Growth**: Every interaction upgrades the business and routes to higher tiers

All gaps from the master agent prompt have been closed. The platform is now a complete business generation + monetization + affiliate engine.

## Installation Instructions

See `INSTALL.md`

## VPS Deployment Guide

See `DEPLOY.md`

## Security Recommendations

See `SECURITY.md`

---

**Ready for future expansion** into full delivery network (Phase 2+).

All code is production-grade, follows Laravel best practices, and is optimized for South African market.