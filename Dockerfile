# Stage 1: Base image for both development and production
FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-root --only main

# Copy application code
COPY app/ ./app/

# Stage 2: Development
FROM base AS development

# Install development dependencies
RUN poetry install --no-root

# Expose port
EXPOSE 8000

# Command is set in docker-compose.yml for hot-reload
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 3: Production (optional, not used in local dev)
FROM base AS production

# Install only production dependencies
RUN poetry install --no-root --only main

# Expose port
EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]