# AI Aggregator Telegram Bot

AI Aggregator is a Telegram-first AI bot platform with a FastAPI backend and provider integrations.

## Tech Stack
- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL
- Redis
- Alembic
- Telegram bot runtime
- Docker Compose

## Setup
1. Clone the repository.
2. Copy env file:
   ```bash
   cp .env.example .env
   ```
3. Fill in `.env` values.
4. Bootstrap services:
   ```bash
   ./scripts/bootstrap.sh
   ```
5. Start full stack:
   ```bash
   docker compose -f infra/docker-compose.yml up --build
   ```

## Manual migrations
Run Alembic from the backend directory (single source of truth: `backend/alembic.ini`):

```bash
cd backend && PYTHONPATH=. alembic -c alembic.ini upgrade head
```

## Project Structure
- `backend/` — FastAPI app, database layer, providers, workers, alembic migrations.
- `telegram_bot/` — existing Telegram bot codebase kept as-is for phase 1 migration.
- `infra/` — docker compose files.
- `scripts/` — bootstrap, lint, tests, seed scripts.
- `docs/` — project documentation and future plans.
