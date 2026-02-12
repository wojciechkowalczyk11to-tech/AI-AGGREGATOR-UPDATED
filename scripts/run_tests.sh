#!/usr/bin/env bash
set -e
pytest backend/tests/ telegram_bot/tests/ -v --tb=short
