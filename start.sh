#!/bin/bash
# Скрипт запуска бота для Render
cd "$(dirname "$0")"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python3 src/main.py

