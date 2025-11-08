# Image Frame API

Production-grade image frame API for scientific/geological data visualization.

## Features

- **Maximum Compression**: gzip level 9 for 16% better storage efficiency
- **On-Demand Colormaps**: Apply colormaps at request time (viridis, plasma, hot, cool, etc.)
- **Production Ready**: Type safety, comprehensive tests, monitoring, structured logging

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Using Docker (Recommended)

```bash
# Build and start services
make docker-build
make docker-up

# Ingest CSV data
make ingest CSV=data/data.csv

# Test API
curl "http://localhost:8000/frames?depth_min=9000&depth_max=9100&colormap=viridis&limit=5"
```

### Local Development

```bash
# Install dependencies
make install

# Run tests
make test

# Run API server
make run

# Ingest data
make ingest CSV=data/data.csv
```

## API Endpoints

- `GET /frames` - JSON array response
- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe (checks database)
- `GET /swagger` - Interactive API documentation

See [API Documentation](docs/API.md) for details.

## Project Structure

```
image-api/
├── src/image_api/          # Main package
│   ├── config/            # Settings and logging
│   ├── models/            # Database models and schemas
│   ├── clients/           # Database client
│   ├── routers/           # API endpoints
│   ├── utilities/         # Compression, image processing, DB ops
│   └── service.py         # FastAPI application
├── scripts/                # CSV ingestion script
├── tests/                  # Test suite
├── monitoring/            # Prometheus and Grafana configs
└── docs/                  # Documentation
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/image_frames
COMPRESSION_LEVEL=9
IMAGE_RESIZED_WIDTH=150
```

## Performance

- **Compression**: 70% storage reduction with level 9
- **Concurrent Requests**: Supports multiple concurrent requests with connection pooling

## Testing

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=src/image_api --cov-report=html

# Run specific test file
pytest tests/test_compression.py
```

Target: 80%+ test coverage

## Monitoring & Logging

- **Prometheus**: http://localhost:9090 (Metrics)
- **Loki**: http://localhost:3100 (Log Aggregation)
- **Grafana**: http://localhost:3000 (admin/admin)
  - Pre-configured datasources: Prometheus, Loki
  - Logs dashboard with real-time viewing
  - Metrics dashboard for performance monitoring
- **Promtail**: Collects logs from all containers
- **Metrics**: Available at `/metrics` endpoint
- **Structured Logging**: JSON format for easy parsing

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Design decisions and tradeoffs
- [API Reference](docs/API.md) - Endpoint documentation
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment

## Development

```bash
# Format code
make format

# Lint code
make lint

# Run tests
make test

# Clean temporary files
make clean
```

## Technology Stack

- **Python**: 3.11+
- **Framework**: FastAPI (async)
- **Database**: PostgreSQL 15+ (asyncpg)
- **ORM**: SQLAlchemy 2.0 (async)
- **Package Manager**: UV
- **Image Processing**: Pillow, NumPy, matplotlib
- **Monitoring**: Prometheus, Grafana
- **Testing**: pytest, pytest-asyncio, httpx

## License

[Your License Here]

## Contributing

[Contributing Guidelines]

