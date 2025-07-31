# Production Deployment Guide for careersgraph.com

## 🌐 Domain Setup Complete
- Domain: careersgraph.com
- Application updated to use "CareersGraph" branding
- Django ALLOWED_HOSTS configured for your domain

## 🚀 Deployment Options for careersgraph.com

### Option 1: Railway (Recommended)
1. **Sign up**: Go to [railway.app](https://railway.app)
2. **Connect GitHub**: Link your GitHub account
3. **Deploy**: Select "Deploy from GitHub repo" → `yin-se/CareersGraph`
4. **Add Services**:
   - PostgreSQL database
   - Redis cache
5. **Environment Variables**:
   ```
   SECRET_KEY=your-super-secret-production-key
   DEBUG=False
   DATABASE_URL=[auto-provided by Railway PostgreSQL]
   REDIS_URL=[auto-provided by Railway Redis]
   ALLOWED_HOSTS=careersgraph.com,www.careersgraph.com,.careersgraph.com
   ```
6. **Custom Domain**: Add careersgraph.com in Railway settings
7. **SSL**: Automatically provided by Railway

### Option 2: DigitalOcean App Platform
1. **Create account**: [digitalocean.com](https://digitalocean.com)
2. **App Platform**: Create new app from GitHub
3. **Select repo**: yin-se/CareersGraph
4. **Add components**:
   - Web service (Django app)
   - Database (PostgreSQL)
   - Redis cache
5. **Custom domain**: Point careersgraph.com to your app

### Option 3: AWS Lightsail
1. **Create instance**: Ubuntu 20.04 LTS
2. **Install dependencies**: Python, PostgreSQL, Redis, Nginx
3. **Clone repository**: `git clone https://github.com/yin-se/CareersGraph.git`
4. **Configure Nginx**: Reverse proxy to Django
5. **SSL certificate**: Use Let's Encrypt/Certbot
6. **Domain setup**: Point DNS to Lightsail IP

## 🛠️ Pre-Deployment Testing

### 1. Local Testing with Production Settings
```bash
# Set production environment
export DEBUG=False
export SECRET_KEY="test-production-key"
export ALLOWED_HOSTS="localhost,careersgraph.com"

# Test the application
python manage.py runserver
```

### 2. Check Static Files
```bash
# Collect static files for production
python manage.py collectstatic --noinput
```

### 3. Database Migration Test
```bash
# Test migrations
python manage.py makemigrations --dry-run
python manage.py migrate --plan
```

## 🔧 Production Environment Variables

Create these environment variables in your deployment platform:

```bash
# Django Core
SECRET_KEY=your-super-secret-production-key-min-50-chars
DEBUG=False
ALLOWED_HOSTS=careersgraph.com,www.careersgraph.com,.careersgraph.com

# Database (provided by hosting platform)
DATABASE_URL=postgresql://user:password@host:port/database
DATABASE_NAME=careersgraph_prod
DATABASE_USER=careersgraph_user
DATABASE_PASSWORD=secure-production-password
DATABASE_HOST=db-host
DATABASE_PORT=5432

# Redis (provided by hosting platform)
REDIS_URL=redis://redis-host:6379/0
CELERY_BROKER_URL=redis://redis-host:6379/0
CELERY_RESULT_BACKEND=redis://redis-host:6379/0

# Security (for HTTPS)
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# LinkedIn Scraping (Optional)
SCRAPING_MIN_DELAY=3.0
SCRAPING_MAX_DELAY=7.0
SCRAPING_REQUESTS_PER_MINUTE=5
SCRAPING_PROFILES_PER_SESSION=25
```

## 🗄️ Database Setup

### Initial Setup Commands
```bash
# After deployment, run these commands:
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py setup_weekly_scraping
```

### Sample Data (Optional)
```bash
# Add some sample universities for testing
python manage.py shell
>>> from core.models import University
>>> University.objects.create(name="Stanford University", country="USA", city="Stanford")
>>> University.objects.create(name="Harvard University", country="USA", city="Cambridge")
>>> University.objects.create(name="MIT", country="USA", city="Cambridge")
```

## 🔒 Security Checklist

- ✅ DEBUG=False in production
- ✅ Strong SECRET_KEY (50+ random characters)
- ✅ HTTPS enabled (SSL certificate)
- ✅ Secure cookie settings
- ✅ ALLOWED_HOSTS properly configured
- ✅ Database credentials secured
- ✅ Rate limiting enabled for scraping
- ✅ Error logging configured

## 🌍 DNS Configuration

Point your domain to your hosting platform:

### For Railway/Render:
1. Add CNAME record: `www` → `your-app.railway.app`
2. Add A record: `@` → provided IP address

### For DigitalOcean:
1. Add A record: `@` → your droplet IP
2. Add CNAME record: `www` → `@`

## 📊 Monitoring & Maintenance

### Health Check Endpoint
Add to `core/urls.py`:
```python
path('health/', views.health_check, name='health-check'),
```

### Logging Configuration
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'careersgraph.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 🚦 Go-Live Checklist

- [ ] Domain DNS configured
- [ ] SSL certificate active
- [ ] Database migrated
- [ ] Static files collected
- [ ] Admin user created
- [ ] Environment variables set
- [ ] Celery workers running
- [ ] Redis cache working
- [ ] Health checks passing
- [ ] Error monitoring setup
- [ ] Backup strategy implemented

## 🔧 Post-Deployment

1. **Test all functionality**:
   - University search
   - Career path exploration
   - Profile matching
   - API endpoints

2. **Monitor performance**:
   - Database query times
   - API response times
   - Memory usage
   - Error rates

3. **Set up monitoring**:
   - Uptime monitoring
   - Error tracking (Sentry)
   - Performance monitoring

Your CareersGraph application is now ready for production deployment at careersgraph.com! 🚀