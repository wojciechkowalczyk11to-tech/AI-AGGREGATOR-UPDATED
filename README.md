# JARVIS AI Aggregator

JARVIS AI Aggregator to Telegram-first bot, który agreguje wielu dostawców LLM i udostępnia ich przez jeden spójny interfejs czatu.

## Najważniejsze funkcje

- Multi-provider: Gemini, DeepSeek, Groq, OpenRouter, Grok.
- RBAC (DEMO i FULL_ACCESS) z kontrolą uprawnień.
- Płatności Telegram Stars i obsługa planów.
- Auto-routing modeli i fallback między providerami.
- Circuit breaker dla niestabilnych integracji.
- Tracking użycia i kosztów per użytkownik.

## Quick Start

1. Sklonuj repozytorium.
2. Skopiuj konfigurację: `cp .env.example .env`.
3. Uzupełnij klucze API i zmienne środowiskowe.
4. Uruchom usługi: `docker compose up`.

## Komendy Telegram

- `/start`
- `/unlock`
- `/help`
- `/mode`
- `/whoami`
- `/usage`
- `/subscribe`
- `/plan`
- `/admin`
- `/invite`

## Stack technologiczny

- FastAPI
- python-telegram-bot
- PostgreSQL
- Redis
- Docker

## Architektura

Monorepo zawiera trzy główne obszary:

- `backend/` — API, logika biznesowa, modele, migracje.
- `telegram_bot/` — bot Telegram i warstwa integracyjna.
- `infra/` — pliki docker-compose i konfiguracja uruchomieniowa.
