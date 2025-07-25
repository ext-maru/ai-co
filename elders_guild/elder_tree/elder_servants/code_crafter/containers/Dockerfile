# Elder Tree v2 - Multi-stage Dockerfile
# Base image with Python 3.11
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

# Create application directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root --no-dev

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Install application
RUN poetry install --only-root

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Create non-root user
RUN useradd -m -u 1000 elderuser && chown -R elderuser:elderuser /app
USER elderuser

# Default command (will be overridden by service-specific commands)
CMD ["python", "-m", "elder_tree"]