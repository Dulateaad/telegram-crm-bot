"""Конфигурация бота"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError('TELEGRAM_BOT_TOKEN не установлен. Установите переменную окружения TELEGRAM_BOT_TOKEN в Render Dashboard → Environment Variables')

# Firebase
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'studio-3898272712-a12a4')
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', './firebase-credentials.json')

# Роли пользователей
ADMIN_USER_IDS = [int(uid) for uid in os.getenv('ADMIN_USER_IDS', '').split(',') if uid]
LOGIST_USER_IDS = [int(uid) for uid in os.getenv('LOGIST_USER_IDS', '').split(',') if uid]
OPERATOR_USER_IDS = [int(uid) for uid in os.getenv('OPERATOR_USER_IDS', '').split(',') if uid]

# Web App URL (React Mini App)
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://your-mini-app-url.com')

# Расписание задач (UTC)
SCHEDULE_MOVE_TO_TODAY = '07:30'  # Перекат завтра → сегодня
SCHEDULE_MORNING_REPORT = '09:00'  # Утренний отчет
SCHEDULE_DAY_REPORT = '20:00'      # Сводка дня
SCHEDULE_SLA_CHECK = '*/10'        # Каждые 10 минут

# SLA таймеры (в минутах)
SLA_NO_ANSWER_RETRY = 30  # Повторный звонок через 30 мин
SLA_BAD_NUMBER_ESCALATION = 60  # Эскалация плохого номера через 60 мин

# Redis (опционально)
REDIS_URL = os.getenv('REDIS_URL')

# Google Sheets (опционально)
GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')

