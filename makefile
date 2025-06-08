.PHONY: help build up down logs restart clean backup restore db-check db-reset

# Standardziel
help:
	@echo "🚀 Options Tracker - Docker Management"
	@echo "======================================"
	@echo ""
	@echo "Verfügbare Befehle:"
	@echo "  make build     - Container bauen"
	@echo "  make up        - Container starten"
	@echo "  make down      - Container stoppen"
	@echo "  make restart   - Container neu starten"
	@echo "  make logs      - Live-Logs anzeigen"
	@echo "  make clean     - Nicht verwendete Docker-Objekte löschen"
	@echo ""
	@echo "Datenbank-Befehle:"
	@echo "  make db-check  - Datenbankstatus prüfen"
	@echo "  make db-reset  - Datenbank zurücksetzen"
	@echo "  make backup    - Datenbank-Backup erstellen"
	@echo "  make restore   - Backup wiederherstellen"
	@echo ""
	@echo "Zugriff: http://localhost:8501"

# Container bauen
build:
	@echo "🔨 Baue Docker Container..."
	docker-compose build --no-cache

# Container starten
up:
	@echo "🚀 Starte Options Tracker..."
	docker-compose up -d
	@echo "✅ Options Tracker läuft auf http://localhost:8501"

# Container stoppen
down:
	@echo "🛑 Stoppe Options Tracker..."
	docker-compose down

# Live-Logs anzeigen
logs:
	@echo "📊 Live-Logs (Ctrl+C zum Beenden):"
	docker-compose logs -f options-tracker

# Container neu starten
restart:
	@echo "🔄 Starte Options Tracker neu..."
	docker-compose restart options-tracker
	@echo "✅ Neustart abgeschlossen"

# Aufräumen
clean:
	@echo "🧹 Räume Docker-System auf..."
	docker system prune -f
	docker volume prune -f

# Status anzeigen
status:
	@echo "📊 Container-Status:"
	docker-compose ps

# Datenbankstatus prüfen
db-check:
	@echo "📊 Prüfe Datenbankstatus..."
	docker-compose exec options-tracker python test_db.py

# Datenbanktest mit Wartezeit
db-test:
	@echo "🧪 Führe vollständigen Datenbanktest aus..."
	docker-compose exec options-tracker python test_db.py wait

# Datenbank zurücksetzen
db-reset:
	@echo "⚠️  Setze Datenbank zurück..."
	@read -p "Sind Sie sicher? (y/N): " confirm && [ "$$confirm" = "y" ]
	docker-compose exec options-tracker python init_db.py reset

# Manuelles Backup erstellen
backup:
	@echo "💾 Erstelle Datenbank-Backup..."
	@timestamp=$$(date +%Y%m%d_%H%M%S) && \
	docker-compose exec options-tracker sqlite3 /app/data/options_tracker.db ".backup /app/backups/manual_backup_$$timestamp.db" && \
	echo "✅ Backup erstellt: manual_backup_$$timestamp.db"

# Backup wiederherstellen
restore:
	@echo "📁 Verfügbare Backups:"
	@ls -la ./backups/*.db 2>/dev/null || echo "Keine Backups gefunden"
	@echo ""
	@read -p "Backup-Dateiname (ohne Pfad): " backup_file && \
	if [ -f "./backups/$$backup_file" ]; then \
		echo "🔄 Stelle Backup wieder her: $$backup_file"; \
		docker-compose exec options-tracker cp "/app/backups/$$backup_file" "/app/data/options_tracker.db" && \
		echo "✅ Backup erfolgreich wiederhergestellt"; \
	else \
		echo "❌ Backup-Datei nicht gefunden: $$backup_file"; \
	fi

# Entwicklungsmodus (mit automatischen Neustarts)
dev:
	@echo "🔧 Starte im Entwicklungsmodus..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Shell im Container öffnen
shell:
	@echo "🐚 Öffne Shell im Container..."
	docker-compose exec options-tracker /bin/bash

# Container-Logs herunterladen
download-logs:
	@timestamp=$$(date +%Y%m%d_%H%M%S) && \
	docker-compose logs options-tracker > "logs_$$timestamp.txt" && \
	echo "✅ Logs gespeichert in: logs_$$timestamp.txt"
