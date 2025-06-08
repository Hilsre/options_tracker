FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN if [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        pip install --no-cache-dir streamlit pandas sqlite3 datetime; \
    fi

COPY . .

RUN mkdir -p /app/data /app/logs

EXPOSE 8501

ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

RUN echo '#!/bin/bash\n\
echo "🚀 Starte Options Tracker..."\n\
echo "📊 Initialisiere Datenbank..."\n\
python init_db.py\n\
echo "✅ Datenbank bereit!"\n\
echo "🌐 Starte Streamlit Server..."\n\
exec streamlit run 1_Overview.py --server.port=8501 --server.address=0.0.0.0' > /app/start.sh

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
