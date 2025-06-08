# Multi-stage build für optimale Image-Größe
FROM python:3.11-slim as builder

# Build-Dependencies installieren
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python-Dependencies installieren
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production Stage
FROM python:3.11-slim

# Non-root User erstellen für Sicherheit
RUN useradd --create-home --shell /bin/bash appuser

# Arbeitsverzeichnis setzen
WORKDIR /app

# Python-Packages von Builder kopieren
COPY --from=builder /root/.local /home/appuser/.local

# App-Code kopieren
COPY . .

# Ordner für persistent data erstellen
RUN mkdir -p /app/data && \
    mkdir -p /app/backups && \
    chown -R appuser:appuser /app

# User wechseln
USER appuser

# PATH für lokale Python-Packages setzen
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Healthcheck mit curl installieren
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/_stcore/health', timeout=10)" || exit 1

# Port freigeben
EXPOSE 8501

# Startbefehl
CMD ["streamlit", "run", "1_Overview.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--server.fileWatcherType=none"]
