# Installation Guide - Ubernie

## Prerequisites
- PHP 8.4+
- Composer
- MySQL 8.0+
- Node.js 20+
- Meilisearch (self-hosted)

## Steps

1. Clone repo
2. `cp .env.example .env`
3. `composer install`
4. `npm install && npm run build`
5. Configure `.env` (DB, Meilisearch, APP_URL=https://www.ubernie.co.za)
6. `php artisan key:generate`
7. `php artisan migrate --seed`
8. `php artisan meilisearch:create-index businesses`
9. Set up queue worker + cron for Laravel scheduler
10. Configure Nginx + PHP-FPM (see DEPLOY.md)

Run `php artisan serve` for local development.