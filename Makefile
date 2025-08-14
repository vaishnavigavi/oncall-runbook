.PHONY: help dev web ingest selfcheck clean build

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Start all services in development mode
	@echo "Starting all services in development mode..."
	docker compose up --build

web: ## Start only the web service
	@echo "Starting web service..."
	docker compose up web --build

ingest: ## Run data ingestion process
	@echo "Running data ingestion..."
	docker compose exec api python /app/app/scripts/ingest.py

selfcheck: ## Verify all services are running correctly
	@echo "Performing self-check..."
	@echo "Checking API health..."
	@curl -f http://localhost:8000/health || (echo "API not responding" && exit 1)
	@echo "Checking web service..."
	@curl -f http://localhost:3000 || (echo "Web service not responding" && exit 1)
	@echo "Checking data directories..."
	@docker compose exec api ls -la /app/data/docs || (echo "Data docs not accessible" && exit 1)
	@docker compose exec api ls -la /app/data/index || (echo "Index directory not accessible" && exit 1)
	@docker compose exec api ls -la /app/data/mock/logs || (echo "Mock logs not accessible" && exit 1)
	@echo "✅ All services are running correctly!"

build: ## Build all Docker images
	@echo "Building Docker images..."
	docker compose build

clean: ## Clean up Docker containers and images
	@echo "Cleaning up..."
	docker compose down -v
	docker system prune -f

logs: ## Show logs for all services
	docker compose logs -f

api-logs: ## Show logs for API service
	docker compose logs -f api

web-logs: ## Show logs for web service
	docker compose logs -f web
