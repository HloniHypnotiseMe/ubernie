# Security Recommendations - Ubernie

## Core Security
- Always keep Laravel, PHP, MySQL, and dependencies updated
- Use strong passwords and 2FA for admin accounts
- Enable CSRF protection (default in Laravel)
- Use Laravel Sanctum or Passport for API authentication
- Rate limit all public endpoints
- Validate and sanitize all user input
- Store sensitive files outside web root

## Database
- Use prepared statements (Eloquent/Query Builder)
- Never expose raw IDs in URLs where possible
- Regular security audits of migrations

## Frontend
- CSP headers
- XSS protection via Blade escaping
- Alpine.js used safely

## Production Hardening
- Disable directory listing
- Hide PHP version
- Use HTTPS everywhere (HSTS)
- Regular vulnerability scanning with `composer audit`
- Implement login throttling

## South African Compliance
- POPIA compliant data handling
- Clear privacy policy and terms

## Future
- Add WAF (Web Application Firewall) on VPS
- Implement audit logging for admin actions