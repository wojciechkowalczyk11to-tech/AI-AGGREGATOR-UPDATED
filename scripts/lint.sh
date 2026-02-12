#!/usr/bin/env bash
set -e
ruff check backend/ telegram_bot/
ruff format --check backend/ telegram_bot/
