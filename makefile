.PHONY: help build up down logs restart clean backup restore db-check db-reset

# Default target
help:
	@echo "🚀 Options Tracker - Docker Management"
	@echo "======================================"
	@echo ""
	@echo "Available Commands:"
	@echo "  make build     - Build container"
	@echo "  make up        - Start container"
	@echo "  make down      - Stop container"
	@echo "  make restart   - Restart container"
	@echo "  make logs      - Show live logs"
	@echo "  make clean     - Remove unused Docker objects"
	@echo ""
	@echo "Database Commands:"
	@echo "  make db-check  - Check database status"
	@echo "  make db-reset  - Reset database"
	@echo "  make backup    - Create database backup"
	@echo "  make restore   - Restore backup"
	@echo ""
	@echo "Access: http://localhost:8501"

# Build container
build:
	@echo "🔨 Building Docker container..."
	docker-compose build --no-cache

# Start container
up:
	@echo "🚀 Starting Options Tracker..."
	docker-compose up -d
	@echo "✅ Options Tracker running at http://localhost:8501"

# Stop container
down:
	@echo "🛑 Stopping Options Tracker..."
	docker-compose down

# Show live logs
logs:
	@echo "📊 Live logs (Ctrl+C to stop):"
	docker-compose logs -f options-tracker

# Restart container
restart:
	@echo "🔄 Restarting Options Tracker..."
	docker-compose restart options-tracker
	@echo "✅ Restart complete"

# Clean up
clean:
	@echo "🧹 Cleaning Docker system..."
	docker system prune -f
	docker volume prune -f

# Show status
status:
	@echo "📊 Container status:"
	docker-compose ps

# Check database status
db-check:
	@echo "📊 Checking database status..."
	docker-compose exec options-tracker python init_db.py check

# Reset database
db-reset:
	@echo "⚠️  Resetting database..."
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	docker-compose exec options-tracker python init_db.py reset

# Create manual backup
backup:
	@echo "💾 Creating database backup..."
	@timestamp=$$(date +%Y%m%d_%H%M%S) && \
	docker-compose exec options-tracker sqlite3 /app/data/options_tracker.db ".backup /app/backups/manual_backup_$$timestamp.db" && \
	echo "✅ Backup created: manual_backup_$$timestamp.db"

# Restore backup
restore:
	@echo "📁 Available backups:"
	@ls -la ./backups/*.db 2>/dev/null || echo "No backups found"
	@echo ""
	@read -p "Backup filename (without path): " backup_file && \
	if [ -f "./backups/$$backup_file" ]; then \
		echo "🔄 Restoring backup: $$backup_file"; \
		docker-compose exec options-tracker cp "/app/backups/$$backup_file" "/app/data/options_tracker.db" && \
		echo "✅ Backup successfully restored"; \
	else \
		echo "❌ Backup file not found: $$backup_file"; \
	fi

# Development mode (with automatic restarts)
dev:
	@echo "🔧 Starting in development mode..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Open shell in container
shell:
	@echo "🐚 Opening shell in container..."
	docker-compose exec options-tracker /bin/bash

# Download container logs
download-logs:
	@timestamp=$$(date +%Y%m%d_%H%M%S) && \
	docker-compose logs options-tracker > "logs_$$timestamp.txt" && \
	echo "✅ Logs saved in: logs_$$timestamp.txt"
