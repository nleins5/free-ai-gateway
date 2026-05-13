FROM python:3.12-slim

WORKDIR /app

# Install Node.js for UI build
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY providers.json .

# Build frontend UI
COPY ui/ ./ui/
WORKDIR /app/ui
RUN npm ci && npm run build
WORKDIR /app

# Hugging Face Spaces use port 7860 by default
ENV PORT=7860
EXPOSE 7860

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
