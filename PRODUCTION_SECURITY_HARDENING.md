# Production Security Hardening Guide

**PHASE 7, PROMPT 11**

## Critical Settings (PHASE 7)

### 1. Environment-Based Configuration
```python
DEBUG = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
```

**Rule**: Never hardcode `DEBUG=True` in production code.

### 2. HTTPS Enforcement
```python
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

**Rule**: Force HTTPS in all production requests.

### 3. Secrets Management
```python
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-key")
```

**Rule**: 
- Store in environment variables
- Rotate periodically
- Never commit to version control
- Use 50+ character random string

### 4. Allowed Hosts
```python
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
```

**Rule**: Explicitly list all domains. Never use `*` in production.

### 5. Database Security
- Use PostgreSQL (not SQLite)
- Strong passwords required
- Not accessible from public internet
- Read replicas for analytics

### 6. Cookie Security
```python
SESSION_COOKIE_SECURE = True      # HTTPS only
SESSION_COOKIE_HTTPONLY = True    # Not available to JS
SESSION_COOKIE_SAMESITE = 'Lax'   # CSRF protection
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
```

### 7. Content Security Policy
```python
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    "script-src": ("'self'",),  # No inline scripts
    "style-src": ("'self'",),
}
```

### 8. Password Requirements
- Minimum 8 characters
- Mix of uppercase, lowercase, numbers, special chars
- Not similar to user attributes
- Not in common password list

## Deployment Checklist

- [ ] DEBUG = False in production
- [ ] ALLOWED_HOSTS configured correctly
- [ ] SECRET_KEY set to secure random value
- [ ] SECURE_SSL_REDIRECT = True
- [ ] SESSION_COOKIE_SECURE = True
- [ ] CSRF_COOKIE_SECURE = True
- [ ] Database credentials in environment variables
- [ ] Redis credentials in environment variables
- [ ] Payment gateway credentials secured
- [ ] AWS S3 credentials for media files
- [ ] Email service configured
- [ ] Logging configured (Sentry recommended)
- [ ] Rate limiting enabled
- [ ] CORS properly configured

## Monitoring & Logging

### Sentry Integration (for error tracking)
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if not DEBUG:
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
    )
```

### Logging Configuration
```python
LOGGING = {
    "version": 1,
    "handlers": {
        "sentry": {
            "level": "ERROR",
            "class": "sentry_sdk.integrations.logging.EventHandler",
        },
    },
}
```

## API Security

### CSRF Protection
- All POST/PUT/DELETE endpoints require CSRF token
- Enabled by default in Django

### Rate Limiting
- Implement per IP, per user limits
- Use middleware: `django-ratelimit`

### API Authentication
- Use JWT or session tokens
- Tokens should expire (default: 1 hour)
- Refresh tokens with longer TTL (7 days)

## Payment Security

### PCI DSS Compliance
- Never store card details
- Use tokenization (Razorpay, Stripe)
- Maintain audit logs for all transactions
- Encrypt sensitive data in transit (TLS 1.2+)

### Webhook Validation
- Verify webhook signature from gateway
- Use idempotency keys
- Log all webhook events
- Implement retry logic with backoff

## Regular Tasks

- [ ] Rotate SECRET_KEY monthly
- [ ] Update dependencies weekly
- [ ] Review security logs daily
- [ ] Database backups (daily)
- [ ] Database encryption (at rest)
- [ ] Monitor failed login attempts
- [ ] Audit user permissions quarterly

## Infrastructure Security

- Database not publicly accessible
- Redis password protected
- Use VPN/SSH for deployments
- WAF (Web Application Firewall) enabled
- DDoS protection enabled
- Backup encrypted and tested

## Incident Response

1. Immediately isolate affected systems
2. Notify security team
3. Review logs for scope
4. Remediate vulnerability
5. Deploy patch
6. Post-incident review
7. Update security procedures
