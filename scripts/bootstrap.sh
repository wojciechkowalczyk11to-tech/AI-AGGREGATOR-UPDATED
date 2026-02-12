#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
fi

docker compose -f infra/docker-compose.yml up -d postgres redis
sleep 5
cd backend
PYTHONPATH=. alembic -c alembic.ini upgrade head
cd ..
PYTHONPATH=backend python scripts/seed_users.py

echo 'Bootstrap complete'
