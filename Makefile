.PHONY: help install test lint format run docker-build docker-up docker-down docker-logs start stop status reset-db clean all db-init db-status ingest ingest-docker clear-db clear-db-docker

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using UV
	uv sync

test: ## Run tests with coverage
	pytest

test-watch: ## Run tests in watch mode
	pytest-watch

lint: ## Run linters (ruff, mypy)
	ruff check src scripts tests
	mypy src scripts

format: ## Format code with ruff
	ruff format src scripts tests
	ruff check --fix src scripts tests

run: ## Run the API server
	uv run uvicorn image_api.service:app --reload --host 0.0.0.0 --port 8000

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start all services
	@echo "Cleaning up any old containers..."
	@docker-compose down 2>/dev/null || true
	@docker rm -f image-api-postgres image-api-service image-api-prometheus image-api-grafana 2>/dev/null || true
	@docker rm -f image_api_db image_api_service image_api_prometheus image_api_grafana 2>/dev/null || true
	@echo "Starting all services..."
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

start: ## Build and start all systems (PostgreSQL, API, Prometheus, Grafana)
	@echo "Building Docker images..."
	docker-compose build --no-cache api
	@echo "Starting all services..."
	docker-compose up -d --force-recreate --remove-orphans
	@echo "Waiting for services to be ready..."
	@sleep 5
	@timeout=60; \
	api_ready=0; \
	while [ $$timeout -gt 0 ] && [ $$api_ready -eq 0 ]; do \
		if command -v curl > /dev/null 2>&1; then \
			curl -sf http://localhost:8000/health > /dev/null 2>&1 && api_ready=1 || true; \
		else \
			docker-compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" > /dev/null 2>&1 && api_ready=1 || true; \
		fi; \
		if [ $$api_ready -eq 1 ]; then \
			echo "✓ API is ready"; \
			break; \
		fi; \
		sleep 2; \
		timeout=$$((timeout - 2)); \
	done; \
	if [ $$api_ready -eq 0 ]; then \
		echo "⚠ Timeout waiting for API to be ready (check logs with: make docker-logs)"; \
	fi
	@echo ""
	@echo "All systems are running!"
	@echo "  API:        http://localhost:8000"
	@echo "  API Docs:   http://localhost:8000/swagger"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Loki:       http://localhost:3100"
	@echo "  Grafana:    http://localhost:3000 (admin/admin)"
	@echo ""
	@echo "To view logs: make docker-logs"
	@echo "To check status: make status"
	@echo "To stop:      make stop"

stop: ## Stop all services
	docker-compose down
	@echo "All services stopped"

reset-db: ## Reset database (removes volume and recreates)
	@echo "Stopping services and removing volumes..."
	docker-compose down -v
	@echo "Database volume reset. Run 'make start' to recreate with fresh database."

test-db-connection: ## Test database connection from API container
	@echo "Testing database connection..."
	@docker-compose exec -T api python -c "import asyncio; from image_api.clients.database import db_client; db_client.initialize(); print('✓ Database connection successful' if asyncio.run(db_client.health_check()) else '✗ Database connection failed')" || echo "✗ Failed to test connection"

status: ## Show status of all services
	@echo "Service Status:"
	@docker-compose ps
	@echo ""
	@echo "Health Checks:"
	@echo -n "  API:        "
	@if command -v curl > /dev/null 2>&1; then \
		curl -sf http://localhost:8000/health > /dev/null 2>&1 && echo "✓ Healthy" || echo "✗ Unhealthy"; \
	else \
		docker-compose exec -T api python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" > /dev/null 2>&1 && echo "✓ Healthy" || echo "✗ Unhealthy"; \
	fi
	@echo -n "  Database:   "
	@docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1 && echo "✓ Ready" || echo "✗ Not Ready"

docker-logs: ## Show logs from all services
	docker-compose logs -f

docker-logs-api: ## Show logs from API service
	docker-compose logs -f api

db-init: ## Initialize database tables (via API endpoint)
	@echo "Initializing database tables..."
	@curl -X POST http://localhost:8000/init -H "Content-Type: application/json" | jq || echo "Failed to initialize database. Make sure the API is running."

db-status: ## Check database status
	@echo "Checking database status..."
	@curl -s http://localhost:8000/ready | jq || echo "Failed to check database status. Make sure the API is running."

clear-db: ## Clear all data from database (usage: make clear-db)
	@echo "Checking if Docker containers are running..."
	@if docker-compose ps postgres | grep -q "Up"; then \
		echo "Docker containers detected. Using Docker to clear database..."; \
		$(MAKE) clear-db-docker; \
	else \
		echo "Docker containers not running. Attempting local database clearing..."; \
		echo "Note: This requires local PostgreSQL or correct DATABASE_URL environment variable."; \
		DATABASE_URL="$${DATABASE_URL:-postgresql+asyncpg://postgres:postgres@localhost:5432/image_frames}" \
		uv run python -m scripts.clear_database || ( \
			echo ""; \
			echo "Clearing failed. To use Docker (recommended):"; \
			echo "  1. Start containers: make docker-up"; \
			echo "  2. Run: make clear-db-docker"; \
			exit 1 \
		); \
	fi

clear-db-docker: ## Clear all data from database via Docker container
	@echo "Clearing database in Docker container..."
	@docker exec image-api-service python -m scripts.clear_database

ingest: ## Ingest CSV data (usage: make ingest CSV=data/data.csv)
	@if [ -z "$(CSV)" ]; then \
		echo "Usage: make ingest CSV=data/data.csv"; \
		exit 1; \
	fi
	@if [ ! -f "$(CSV)" ]; then \
		echo "Error: CSV file not found: $(CSV)"; \
		echo "Current directory: $$(pwd)"; \
		exit 1; \
	fi
	@echo "Checking if Docker containers are running..."
	@if docker-compose ps postgres | grep -q "Up"; then \
		echo "Docker containers detected. Using Docker ingestion for better compatibility..."; \
		$(MAKE) ingest-docker CSV=$(CSV); \
	else \
		echo "Docker containers not running. Attempting local ingestion..."; \
		echo "Note: This requires local PostgreSQL or correct DATABASE_URL environment variable."; \
		DATABASE_URL="$${DATABASE_URL:-postgresql+asyncpg://postgres:postgres@localhost:5432/image_frames}" \
		uv run python -m scripts.ingest_csv "$(CSV)" || ( \
			echo ""; \
			echo "Ingestion failed. To use Docker (recommended):"; \
			echo "  1. Start containers: make docker-up"; \
			echo "  2. Run: make ingest-docker CSV=$(CSV)"; \
			exit 1 \
		); \
	fi

ingest-docker: ## Ingest CSV data via Docker container (usage: make ingest-docker CSV=data/data.csv)
	@if [ -z "$(CSV)" ]; then \
		echo "Usage: make ingest-docker CSV=data/data.csv"; \
		exit 1; \
	fi
	@echo "Copying CSV file to container..."
	@docker cp $(CSV) image-api-service:/tmp/ingest.csv
	@echo "Running ingestion in container..."
	@docker exec image-api-service python -m scripts.ingest_csv /tmp/ingest.csv
	@docker exec image-api-service rm /tmp/ingest.csv

clean: ## Clean temporary files
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -r {} + 2>/dev/null || true
	rm -f .coverage

all: ## Set up and start the entire system (install, build, start with monitoring)
	@echo "========================================"
	@echo "Setting up complete system..."
	@echo "========================================"
	@echo ""
	@echo "Step 1/5: Installing dependencies..."
	@$(MAKE) install
	@echo ""
	@echo "Step 2/5: Building Docker images..."
	@$(MAKE) docker-build
	@echo ""
	@echo "Step 3/5: Starting all services..."
	@$(MAKE) docker-up
	@echo ""
	@echo "Step 4/5: Waiting for services to be ready..."
	@echo "Waiting for database..."
	@sleep 3
	@timeout 90 bash -c 'until docker-compose exec -T postgres pg_isready -U postgres -d image_frames > /dev/null 2>&1; do echo -n "."; sleep 2; done' && echo " ✓ Ready" || echo " ⚠ Timeout (container may still be starting)"
	@echo "Waiting for API service..."
	@timeout 90 bash -c 'until curl -sf http://localhost:8000/health > /dev/null 2>&1; do echo -n "."; sleep 2; done' && echo " ✓ Ready" || echo " ⚠ Timeout (check logs: make docker-logs-api)"
	@echo "Waiting for Prometheus..."
	@timeout 45 bash -c 'until curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; do echo -n "."; sleep 2; done' && echo " ✓ Ready" || echo " ⚠ Timeout"
	@echo "Waiting for Grafana..."
	@timeout 45 bash -c 'until curl -sf http://localhost:3000/api/health > /dev/null 2>&1; do echo -n "."; sleep 2; done' && echo " ✓ Ready" || echo " ⚠ Timeout"
	@echo ""
	@echo "Step 5/5: Verifying system health..."
	@echo -n "Checking API health... "
	@curl -sf http://localhost:8000/health > /dev/null 2>&1 && echo "✓ Healthy" || echo "✗ Unhealthy"
	@echo -n "Checking database... "
	@docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1 && echo "✓ Ready" || echo "✗ Not Ready"
	@echo ""
	@echo "========================================"
	@echo "✓ All system is up and running!"
	@echo "========================================"
	@echo ""
	@echo "Service URLs:"
	@echo "  API:        http://localhost:8000"
	@echo "  API Docs:   http://localhost:8000/swagger"
	@echo "  Health:     http://localhost:8000/health"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana:    http://localhost:3000 (admin/admin)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Check database status: make db-status"
	@echo "  2. Initialize database (if needed): make db-init"
	@echo "  3. Ingest data: make ingest CSV=data/data.csv"
	@echo "  4. View logs: make docker-logs"
	@echo "  5. Check status: make status"
	@echo "  6. Run tests: make test"
	@echo "  7. Stop services: make stop"
	@echo ""
	@echo "Note: Database tables are created automatically on API startup."
	@echo "      Use 'make db-init' if you need to recreate them manually."

