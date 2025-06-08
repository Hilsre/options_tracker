# Python 3.11 als Basis (kompatibel mit den meisten Streamlit-Anwendungen)
FROM python:3.11-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten kopieren und installieren
COPY requirements.txt .

# Falls keine requirements.txt vorhanden ist, Standard-Abhängigkeiten installieren
RUN if [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        pip install --no-cache-dir streamlit pandas sqlite3 datetime; \
    fi

# Anwendungscode kopieren
COPY . .

# Verzeichnisse für Daten und Logs erstellen
RUN mkdir -p /app/data /app/logs

# Port für Streamlit freigeben
EXPOSE 8501

# Streamlit-Konfiguration
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Gesundheitsprüfung
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Startup-Script erstellen
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🚀 Starte Options Tracker..."\n\
echo "📊 Initialisiere Datenbank..."\n\
\n\
# Warte bis Datenbank-Datei existiert\n\
mkdir -p /app/data\n\
\n\
# Führe Datenbankinitialisierung aus und warte auf Abschluss\n\
python init_db.py\n\
if [ $? -eq 0 ]; then\n\
    echo "✅ Datenbank erfolgreich initialisiert!"\n\
else\n\
    echo "❌ Fehler bei Datenbankinitialisierung!"\n\
    exit 1\n\
fi\n\
\n\
# Überprüfe ob alle Tabellen existieren\n\
python -c "\n\
import sqlite3\n\
import os\n\
db_path = os.environ.get('\''DATABASE_PATH'\'', '\''/app/data/options_tracker.db'\'')\n\
conn = sqlite3.connect(db_path)\n\
tables = ['\''basis_products'\'', '\''product_types'\'', '\''directions'\'', '\''strike_currencies'\'', '\''actions'\'', '\''products'\'', '\''transactions'\'', '\''settings'\'']\n\
for table in tables:\n\
    cursor = conn.execute(f'\''SELECT COUNT(*) FROM {table}'\'')\n\
    count = cursor.fetchone()[0]\n\
    print(f'\''  ✓ {table}: {count} Einträge'\'')\n\
conn.close()\n\
print('\''🔍 Alle Tabellen erfolgreich überprüft!'\'')\n\
"\n\
\n\
echo "🌐 Starte Streamlit Server..."\n\
exec streamlit run 1_Overview.py --server.port=8501 --server.address=0.0.0.0' > /app/start.sh

# Script ausführbar machen
RUN chmod +x /app/start.sh

# Anwendung über Startup-Script starten
CMD ["/app/start.sh"]
