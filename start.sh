#!/bin/bash

# Detekce docker compose nebo docker-compose
if command -v docker > /dev/null 2>&1 && docker compose version > /dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose > /dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  echo "Chyba: ani 'docker compose', ani 'docker-compose' není nainstalován."
  exit 1
fi

# Spustí všechny služby: app, redis a test
$COMPOSE up --build -d app redis && $COMPOSE run --rm test