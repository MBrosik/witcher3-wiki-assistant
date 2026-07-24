.PHONY: up down build ingest logs clean nuke test lint up-prod down-prod build-prod clean-prod ollama-pull ollama-pull-llm up-local-llm setup-ollama

# Docker Compose (dev)

setup:
	docker compose up -d
	@echo "Waiting for services to be ready..."
	sleep 5
	docker compose exec ollama ollama pull nomic-embed-text
	docker compose run --rm backend python -m src.ingest
	@echo ""
	@echo "✅ Setup complete! Open http://localhost:5173"
	@echo "   To stop: make down"
	@echo "   Local LLM stack: make setup-ollama (and LLM_PROVIDER=ollama in .env)"

# Setup with additional local LLM
setup-ollama:
	docker compose --profile local-llm up -d
	@echo "Waiting for services to be ready..."
	sleep 5
	docker compose exec ollama ollama pull nomic-embed-text
	docker compose exec ollama-llm ollama pull $${OLLAMA_MODEL:-qwen2.5:7b-instruct}
	docker compose run --rm backend python -m src.ingest
	@echo ""
	@echo "✅ Setup complete (local Ollama LLM)! Open http://localhost:5173"
	@echo "   Ensure backend/.env has LLM_PROVIDER=ollama"
	@echo "   To stop: make down"

up:
	docker compose up -d

up-local-llm:
	docker compose --profile local-llm up -d ollama-llm

down:
	docker compose --profile local-llm down

build:
	docker compose build

logs:
	docker compose logs -f

# Docker Compose (prod)

up-prod:
	docker compose -f docker-compose.prod.yml up -d --build

down-prod:
	docker compose -f docker-compose.prod.yml --profile local-llm down

build-prod:
	docker compose -f docker-compose.prod.yml build

clean-prod:
	docker compose -f docker-compose.prod.yml --profile local-llm down -v

# Data Pipeline

ollama-pull:
	docker compose exec ollama ollama pull nomic-embed-text

ollama-pull-llm:
	docker compose --profile local-llm up -d ollama-llm
	docker compose exec ollama-llm ollama pull $${OLLAMA_MODEL:-qwen2.5:7b-instruct}

ingest:
	docker compose run --rm backend python -m src.ingest

# Development

lint-backend:
	docker compose run --rm backend ruff check src/
	docker compose run --rm backend ruff format --check src/

lint-frontend:
	docker compose run --rm frontend npm run lint

lint: lint-backend lint-frontend

typecheck:
	docker compose run --rm frontend npx tsc --noEmit

# Cleanup

clean:
	docker compose --profile local-llm down -v
	rm -rf data/raw/*

nuke:
	docker compose --profile local-llm down -v --rmi all --remove-orphans
	docker compose -f docker-compose.prod.yml --profile local-llm down -v --rmi all --remove-orphans
	rm -rf data/raw/*
