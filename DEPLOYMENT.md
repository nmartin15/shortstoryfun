# Deployment Guide

This guide covers deploying the Short Story Pipeline application to production.

## Prerequisites

- Python 3.9 or higher
- pip
- (Optional) Redis for distributed rate limiting
- (Optional) Nginx or another reverse proxy

## Quick Start

### 1. Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your configuration:
   ```bash
   FLASK_ENV=production
   FLASK_DEBUG=False
   GOOGLE_API_KEY=your_api_key_here
   REDIS_URL=redis://localhost:6379/0  # Optional but recommended
   CORS_ALLOWED_ORIGINS=https://yourdomain.com  # Required if using a frontend
   ```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run with Gunicorn (Production)

```bash
gunicorn -c gunicorn_config.py app:app
```

Or with custom settings:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

## Production Deployment Options

### Option 1: Standalone Gunicorn

**Pros:** Simple, no additional services required  
**Cons:** No reverse proxy, manual SSL setup

```bash
# Start the server
gunicorn -c gunicorn_config.py app:app

# Or with environment variables
export FLASK_ENV=production
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
```

### Option 2: Gunicorn + Nginx (Recommended)

**Pros:** Better performance, SSL termination, static file serving  
**Cons:** Requires Nginx configuration

1. **Install Nginx:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install nginx
   
   # macOS
   brew install nginx
   ```

2. **Configure Nginx** (example: `/etc/nginx/sites-available/shortstory`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       # Redirect HTTP to HTTPS (if using SSL)
       # return 301 https://$server_name$request_uri;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 120s;
       }
       
       # Serve static files directly (optional)
       location /static {
           alias /path/to/ShortStory/static;
           expires 30d;
       }
   }
   ```

3. **Enable the site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/shortstory /etc/nginx/sites-enabled/
   sudo nginx -t  # Test configuration
   sudo systemctl reload nginx
   ```

4. **Start Gunicorn:**
   ```bash
   gunicorn -c gunicorn_config.py app:app
   ```

### Option 3: Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]
```

Build and run:
```bash
docker build -t shortstory .
docker run -p 5000:5000 --env-file .env shortstory
```

### Option 4: Platform-as-a-Service (PaaS)

#### Heroku

1. Create `Procfile`:
   ```
   web: gunicorn -c gunicorn_config.py app:app
   ```

2. Deploy:
   ```bash
   heroku create your-app-name
   heroku config:set GOOGLE_API_KEY=your_key
   heroku config:set FLASK_ENV=production
   git push heroku main
   ```

#### Railway

1. Connect your repository
2. Set environment variables in Railway dashboard
3. Railway will auto-detect and deploy

#### Render

1. Create a new Web Service
2. Connect your repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn -c gunicorn_config.py app:app`
5. Set environment variables

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FLASK_ENV` | Environment mode | `development` | No |
| `FLASK_DEBUG` | Enable debug mode | `False` | No |
| `GOOGLE_API_KEY` | Google Gemini API key | - | Yes (for AI) |
| `REDIS_URL` | Redis connection URL | `memory://` | No |
| `HOST` | Server host | `0.0.0.0` | No |
| `PORT` | Server port | `5000` | No |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed origins for CORS | (empty - no CORS) | No (required if using frontend) |

### Rate Limiting

Rate limiting is configured with Flask-Limiter:

- **Default limits:** 200 requests/day, 50 requests/hour per IP
- **Story generation:** 10 requests/minute per IP
- **Other endpoints:** 100 requests/hour per IP

For production with multiple workers, use Redis:
```bash
REDIS_URL=redis://localhost:6379/0
```

### CORS Configuration

CORS (Cross-Origin Resource Sharing) is configured to only allow requests from specified origins to `/api/*` routes. This provides better security by restricting cross-origin access to API endpoints only.

**Configuration:**
- Set `CORS_ALLOWED_ORIGINS` in your `.env` file with a comma-separated list of allowed origins
- If not set, CORS is disabled (no cross-origin requests allowed)
- CORS only applies to `/api/*` routes, not the entire application

**Examples:**
```bash
# Single origin
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Multiple origins (development + production)
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Multiple production domains
CORS_ALLOWED_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com
```

**Security Notes:**
- Never use `*` (wildcard) in production - always specify exact origins
- Use HTTPS origins in production
- Only include origins you trust and control

### Gunicorn Configuration

Edit `gunicorn_config.py` or set environment variables:

- `GUNICORN_WORKERS`: Number of worker processes (default: CPU count * 2 + 1)
- `GUNICORN_BIND`: Bind address (default: `0.0.0.0:5000`)
- `GUNICORN_ACCESS_LOG`: Access log file (default: stdout)
- `GUNICORN_ERROR_LOG`: Error log file (default: stderr)

## Monitoring

### Health Check

The application provides a health check endpoint:
```bash
curl http://localhost:5000/api/health
```

### Logging

Logs are written to:
- **Development:** Console (stdout/stderr)
- **Production:** Configure via `GUNICORN_ACCESS_LOG` and `GUNICORN_ERROR_LOG`

Log levels:
- `DEBUG`: Development only
- `INFO`: General information
- `WARNING`: Warnings
- `ERROR`: Errors with stack traces

### Performance Monitoring

Consider adding:
- Application Performance Monitoring (APM) tools
- Error tracking (Sentry, Rollbar)
- Metrics collection (Prometheus, Datadog)

## Security Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Use HTTPS (via reverse proxy or load balancer)
- [ ] Set secure `SECRET_KEY` (if using sessions)
- [ ] Configure firewall rules
- [ ] Use Redis for rate limiting (not in-memory)
- [ ] Regularly update dependencies
- [ ] Configure `CORS_ALLOWED_ORIGINS` if deploying a frontend (CORS is restricted to `/api/*` routes only)
- [ ] Set appropriate file permissions

## Troubleshooting

### Rate Limiting Not Working Across Workers

**Problem:** Rate limits reset when using multiple Gunicorn workers with in-memory storage.

**Solution:** Use Redis:
```bash
REDIS_URL=redis://localhost:6379/0
```

### Story Generation Timeouts

**Problem:** Long-running story generation requests timeout.

**Solution:** Increase timeout in `gunicorn_config.py`:
```python
timeout = 300  # 5 minutes
```

### Memory Issues

**Problem:** Application uses too much memory.

**Solution:** 
- Reduce number of workers
- Implement story cleanup/archival
- Ensure database storage is enabled (`USE_DB_STORAGE=true`) - this is the default
- Enable Redis caching (`USE_REDIS_CACHE=true`) to reduce database load

## Storage Configuration

The application supports two storage backends. For detailed information about storage implementation, configuration, and migration, see **[STORAGE_IMPLEMENTATION.md](STORAGE_IMPLEMENTATION.md)**.

**Quick Configuration:**
```bash
USE_DB_STORAGE=true  # Use database storage (default, recommended for production)
USE_REDIS_CACHE=false  # Optional: Enable Redis caching for stories
```

**Database Location:** `data/stories.db`

**Note:** Database storage is enabled by default and recommended for production. File storage (`USE_DB_STORAGE=false`) is suitable for development but not recommended for production with large numbers of stories.

## Backup and Recovery

For detailed backup and recovery procedures, see **[STORAGE_IMPLEMENTATION.md](STORAGE_IMPLEMENTATION.md)**.

**Quick Backup Commands:**

**Database Storage:**
```bash
# Backup SQLite database
cp data/stories.db data/stories-backup-$(date +%Y%m%d).db
```

**File Storage:**
```bash
# Backup stories directory
tar -czf stories-backup-$(date +%Y%m%d).tar.gz stories/
```

## Scaling

For high traffic:

1. **Horizontal scaling:** Deploy multiple instances behind a load balancer
2. **Use Redis:** Required for shared rate limiting across instances
3. **Database storage:** Already enabled by default (`USE_DB_STORAGE=true`)
4. **Redis caching:** Enable with `USE_REDIS_CACHE=true` for frequently accessed stories
5. **CDN:** Use CDN for static assets

## Support

For issues or questions:
- Check logs: `gunicorn_config.py` log settings
- Health check: `/api/health`
- Review error responses: All errors include `error_code` for debugging

