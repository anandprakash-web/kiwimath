# Kiwimath API — production Docker image (v2-only)
# Build:  docker build -t kiwimath-api .
# Run:    docker run -p 8000:8000 kiwimath-api
#
# Content is bundled at build time (v2 in /content-v2).

FROM python:3.12-slim

# Prevent Python from buffering stdout/stderr (important for Cloud Run logs).
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer caching).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY . .

# v2 content (flat JSON/SVG — olympiad-style questions).
ENV KIWIMATH_V2_CONTENT_DIR=/content-v2
ENV PORT=8000

EXPOSE 8000

# Health check for Cloud Run / Docker Compose.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with uvicorn. Cloud Run sets PORT env var.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --log-level info"]
