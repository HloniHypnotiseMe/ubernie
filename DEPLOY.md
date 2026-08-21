# VPS Deployment Guide - Ubernie (No Docker)

## Recommended VPS
- Ubuntu 24.04 LTS
- 4GB+ RAM, 2+ vCPU
- Provider: Any (Hetzner, DigitalOcean, Linode, etc.)

## Production Setup

1. Install LEMP stack (Nginx, MySQL, PHP 8.4)
2. Install Meilisearch (binary or apt)
3. Clone project to /var/www/ubernie
4. Set correct permissions: `chown -R www-data:www-data storage bootstrap/cache`
5. Configure Nginx virtual host with SSL (Let's Encrypt)
6. Supervisor for queue worker
7. Enable OPcache + Redis for sessions/cache (optional but recommended)

## Environment Variables
- Set APP_ENV=production
- APP_DEBUG=false
- Enable HTTPS only

## Monitoring
- Use Laravel Horizon or simple queue:work
- Log rotation for Laravel logs

## Backup Strategy
- Daily mysqldump + file backups to offsite storage

## Zero-Downtime Deployment
- Use git pull + `php artisan migrate` + reload PHP-FPM + `npm run build`