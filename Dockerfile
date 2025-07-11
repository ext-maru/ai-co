# Multi-stage Dockerfile for Elders Guild Platform
FROM python:3.11-slim as base

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
RUN chown -R app:app /app

# Switch to app user
USER app

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v2/system/health || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "libs.elders_guild_api_spec:app", "--host", "0.0.0.0", "--port", "8000"]

# Development stage
FROM base as development
USER root
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov black flake8 mypy
USER app
CMD ["python", "-m", "uvicorn", "libs.elders_guild_api_spec:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production
# Copy only necessary files
COPY --from=base /app/libs /app/libs
COPY --from=base /app/knowledge_base /app/knowledge_base
COPY --from=base /app/database /app/database
COPY --from=base /app/requirements.txt /app/requirements.txt

# Set production environment
ENV ENV=production
ENV PYTHONOPTIMIZE=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run as non-root user
USER app

# Production command
CMD ["python", "-m", "uvicorn", "libs.elders_guild_api_spec:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
