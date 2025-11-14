# Stage 1: Base image for both development and production
FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=2.2.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Copy dependency files first for better caching
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root --no-ansi

# Stage 2: Development
FROM base AS development

# Create non-root user with specific UID for consistency
RUN groupadd -r appuser -g 1000 && useradd -r -u 1000 -g appuser appuser

# Create migrations directory structure with correct permissions
RUN mkdir -p /app/migrations/versions && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser

# Copy application code
COPY --chown=appuser:appuser . .

EXPOSE 8000

# Stage 3: Production
FROM base AS production

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Copy application code
COPY --chown=appuser:appuser . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]