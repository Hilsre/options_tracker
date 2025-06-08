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

# Anwendung starten
CMD ["streamlit", "run", "1_Overview.py", "--server.port=8501", "--server.address=0.0.0.0"]
