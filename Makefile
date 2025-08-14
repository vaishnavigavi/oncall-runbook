.PHONY: dev build up down logs clean test selfcheck

# Development
dev:
	docker compose up --build

# Build containers
build:
	docker compose build

# Start services
up:
	docker compose up -d

# Stop services
down:
	docker compose down

# View logs
logs:
	docker compose logs -f

# Clean up
clean:
	docker compose down -v
	docker system prune -f

# Run tests
test:
	docker compose exec api python -m pytest tests/ -v

# Run selfcheck
selfcheck:
	curl -s http://localhost:8000/selfcheck | jq '.'

# Quick health check
health:
	curl -s http://localhost:8000/health

# KB status check
kb-status:
	curl -s http://localhost:8000/kb/status | jq '.'

# Test RAG query
test-rag:
	curl -X POST "http://localhost:8000/ask/structured" \
		-H "Content-Type: application/json" \
		-d '{"question": "What are the first steps for CPU issues?", "context": ""}' | jq '.'
