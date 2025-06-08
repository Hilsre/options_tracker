# Options Tracker Docker Commands

.PHONY: help build run stop clean logs backup restore

# Default target
help:
	@echo "Available commands:"
	@echo "  build    - Build the Docker image"
	@echo "  run      - Start the application with docker-compose"
	@echo "  stop     - Stop the application"
	@echo "  restart  - Restart the application"
	@echo "  clean    - Remove containers and images"
	@echo "  logs     - Show application logs"
	@echo "  shell    - Open shell in running container"
	@echo "  backup   - Create manual backup"
	@echo "  restore  - List available backups"

# Build the Docker image
build:
	@echo "Building Options Tracker Docker image..."
	docker-compose build --no-cache

# Start the application
run:
	@echo "Starting Options Tracker..."
	docker-compose up -d
	@echo "Application is running at http://localhost:8501"

# Stop the application
stop:
	@echo "Stopping Options Tracker..."
	docker-compose down

# Restart the application
restart: stop run

# Clean up containers and images
clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down --rmi all --volumes --remove-orphans
	docker system prune -f

# Show logs
logs:
	docker-compose logs -f options-tracker

# Open shell in running container
shell:
	docker-compose exec options-tracker bash

# Create manual backup
backup:
	@echo "Creating manual backup..."
	docker-compose exec options-tracker sh -c "timestamp=\$$(date +%Y%m%d_%H%M%S); cp /app/data/options_tracker.db /app/backups/manual_backup_\$$timestamp.db"
	@echo "Backup created in ./backups/"

# List available backups
restore:
	@echo "Available backups:"
	@ls -la ./backups/*.db 2>/dev/null || echo "No backups found"

# Development mode (with file watching)
dev:
	@echo "Starting in development mode..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Health check
health:
	@curl -f http://localhost:8501/_stcore/health && echo "Application is healthy" || echo "Application is not responding"
