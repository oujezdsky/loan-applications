#!/bin/bash
until pg_isready -h db -p 5432 -U myuser; do
  echo "Waiting for Postgres..."
  sleep 2
done

# Spusť migrace
alembic upgrade head

# Spusť app
exec "$@"