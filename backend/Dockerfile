# Production Dockerfile for Render.com
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock* ./

# Install Python dependencies
# Use --no-dev to skip development dependencies
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Download cross-encoder model during build (cached in Docker image)
# This prevents downloading on every container startup
RUN uv run python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Expose port (Render will set PORT environment variable)
EXPOSE 8000

# Run with uvicorn
# Render sets PORT automatically
CMD ["sh", "-c", "uv run uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
