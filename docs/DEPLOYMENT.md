# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- 4GB+ RAM recommended
- 10GB+ disk space for data

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd image-api
cp .env.example .env
# Edit .env with your configuration
```

### 2. Build and Start Services

```bash
make docker-build
make docker-up
```

Or manually:

```bash
docker-compose build
docker-compose up -d
```

### 3. Ingest CSV Data

```bash
# Copy CSV file to data/ directory
cp /path/to/data.csv data/

# Ingest data
docker-compose exec api python -m scripts.ingest_csv /app/data/data.csv
```

Or using Makefile:

```bash
make ingest CSV=data/data.csv
```

### 4. Verify Deployment

```bash
# Check health
curl http://localhost:8000/health

# Check readiness
curl http://localhost:8000/ready

# Test API
curl "http://localhost:8000/frames?depth_min=9000&depth_max=9100&colormap=viridis&limit=5"
```

## Service URLs

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/swagger
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100
- **Grafana**: http://localhost:3000 (admin/admin)

## Configuration

### Environment Variables

Edit `.env` file or set environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/image_frames
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Image Processing
COMPRESSION_LEVEL=9
IMAGE_RESIZED_WIDTH=150
IMAGE_ORIGINAL_WIDTH=200

# API
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
LOG_FORMAT=json
PROMETHEUS_ENABLED=true
```

### Database Configuration

PostgreSQL is configured via `docker-compose.yml`:

- **User**: postgres
- **Password**: postgres (change in production!)
- **Database**: image_frames
- **Port**: 5432

## Production Deployment

### 1. Security Hardening

- Change default PostgreSQL password
- Configure CORS appropriately
- Add rate limiting
- Add authentication (API keys or OAuth2)
- Use HTTPS/TLS
- Set up firewall rules

### 2. Database Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U postgres image_frames > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres image_frames < backup.sql
```

### 3. Monitoring

- Prometheus metrics available at `/metrics`
- Grafana dashboards for visualization
- Set up alerts for:
  - High error rate
  - High latency
  - Database connection failures
  - Disk space usage

### 4. Scaling

**Horizontal Scaling**:
- Run multiple API instances behind load balancer
- Use shared PostgreSQL database
- Configure connection pooling appropriately

**Vertical Scaling**:
- Increase `DATABASE_POOL_SIZE` for more connections
- Monitor memory usage

### 5. Health Checks

Configure your orchestration platform (Kubernetes, etc.) to use:

- **Liveness**: `GET /health`
- **Readiness**: `GET /ready`

## Troubleshooting

### Database Connection Issues

```bash
# Check database status
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec api python -c "from image_api.clients.database import db_client; import asyncio; asyncio.run(db_client.health_check())"
```

### API Not Starting

```bash
# Check API logs
docker-compose logs api

# Check environment variables
docker-compose exec api env | grep DATABASE
```

### Performance Issues

1. **Check database indexes**:
   ```sql
   SELECT * FROM pg_indexes WHERE tablename = 'image_frames';
   ```

2. **Monitor connection pool**:
   - Check Prometheus metrics for connection pool usage
   - Adjust `DATABASE_POOL_SIZE` if needed

3. **Check memory usage**:
   - Should be constant with lazy loading
   - If growing, check for memory leaks

### Data Ingestion Issues

```bash
# Check ingestion logs
python -m scripts.ingest_csv data/data.csv

# Verify data in database
docker-compose exec postgres psql -U postgres image_frames -c "SELECT COUNT(*) FROM image_frames;"
```

## Maintenance

### Update Dependencies

```bash
# Update UV lockfile
uv lock

# Rebuild Docker image
make docker-build
```

### Database Migrations

Currently using SQLAlchemy auto-create. For production:

1. Use Alembic for migrations
2. Version control schema changes
3. Test migrations on staging first

### Log Rotation

Configure log rotation for production:

```yaml
# docker-compose.yml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Backup and Recovery

### Automated Backups

Set up cron job for daily backups:

```bash
0 2 * * * docker-compose exec -T postgres pg_dump -U postgres image_frames | gzip > /backups/image_frames_$(date +\%Y\%m\%d).sql.gz
```

### Recovery

```bash
# Stop services
docker-compose down

# Restore database
docker-compose up -d postgres
docker-compose exec -T postgres psql -U postgres image_frames < backup.sql

# Restart services
docker-compose up -d
```

## Monitoring Setup

### Prometheus

Prometheus is configured via `monitoring/prometheus.yml` and automatically scrapes metrics from the API.

### Loki (Log Aggregation)

Loki collects and stores logs from all services. Configuration is in `monitoring/loki.yml`.

**Features**:
- Centralized log storage
- 7-day retention (configurable)
- Efficient compression
- Queryable via LogQL

### Promtail (Log Shipper)

Promtail collects logs from Docker containers and ships them to Loki. Configuration is in `monitoring/promtail.yml`.

**Features**:
- Automatic Docker log discovery
- JSON log parsing
- Label extraction (level, service, container)
- Real-time log shipping

### Grafana

1. Access Grafana: http://localhost:3000
2. Login: admin/admin
3. Datasources are auto-configured:
   - **Prometheus**: Metrics (http://prometheus:9090)
   - **Loki**: Logs (http://loki:3100)
4. Pre-configured dashboards:
   - **Logs Dashboard**: Real-time log viewing, error rate, log volume by level
5. Create additional dashboards for:
   - Request rate
   - Latency (p50, p95, p99)
   - Error rate
   - Database connections
   - Memory usage

### Log Queries (LogQL)

Example queries in Grafana Explore:

```
# All API logs
{service="api"}

# Error logs only
{service="api", level="ERROR"}

# Logs from specific module
{service="api", logger="image_api.routers.frames"}

# Logs with specific message pattern
{service="api"} |= "database"
```

## Performance Tuning

### Database

```sql
-- Increase shared_buffers
ALTER SYSTEM SET shared_buffers = '256MB';

-- Increase work_mem
ALTER SYSTEM SET work_mem = '16MB';
```

### Application

- Adjust `DATABASE_POOL_SIZE` based on load
- Adjust `STREAM_BATCH_SIZE` for memory/performance tradeoff
- Monitor Prometheus metrics for bottlenecks

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Check health endpoints: `/health`, `/ready`
3. Review documentation: `docs/`
4. Check Prometheus metrics: `/metrics`

