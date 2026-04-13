FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir bcrypt==3.2.2

# Download spaCy model
RUN python -m spacy download fr_core_news_md

# Copy application code
COPY api/ ./api/
COPY etl/ ./etl/
COPY ingestion/ ./ingestion/
COPY ai_services/ ./ai_services/
COPY scrapers/ ./scrapers/
COPY tests/ ./tests/

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
