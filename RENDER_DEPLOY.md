# Деплой Telegram CRM бота на Render

## Подготовка

### 1. Убедитесь, что репозиторий на GitHub

```bash
cd /Users/dulat/telegram-bot-crm
git add .
git commit -m "Подготовка к деплою на Render"
git push origin main
```

### 2. Подготовьте Firebase credentials

Firebase credentials нужно будет добавить через переменные окружения на Render, так как файлы нельзя загружать напрямую.

## Деплой на Render

### Шаг 1: Создайте новый сервис

1. Откройте [Render Dashboard](https://dashboard.render.com/)
2. Нажмите **"New +"** → **"Background Worker"**
3. Подключите репозиторий GitHub: `Dulateaad/telegram-crm-bot`

### Шаг 2: Настройте сервис

**Basic Settings:**
- **Name:** `telegram-crm-bot`
- **Environment:** `Python 3`
- **Region:** Выберите ближайший (например, `Frankfurt`)
- **Branch:** `main`
- **Root Directory:** (оставьте пустым)
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python3 src/main.py`

### Шаг 3: Настройте переменные окружения

В разделе **"Environment Variables"** добавьте:

#### Обязательные:
```
TELEGRAM_BOT_TOKEN=8271971457:AAE9Of7FpMWK0GFgzjxf-XmI0lU3SuZkDVA
FIREBASE_PROJECT_ID=studio-3898272712-a12a4
WEB_APP_URL=https://studio--studio-3898272712-a12a4.us-central1.hosted.app
```

#### Firebase Credentials (важно!)

Так как Render не поддерживает загрузку файлов напрямую, нужно добавить credentials как переменную окружения:

1. Откройте ваш `firebase-credentials.json` файл
2. Скопируйте весь JSON
3. В Render добавьте переменную:
   ```
   FIREBASE_CREDENTIALS_JSON=<вставьте весь JSON здесь>
   ```

Затем обновите `src/config.py` чтобы читать из переменной окружения:

```python
import json
import os

# Читаем credentials из переменной окружения или файла
if os.getenv('FIREBASE_CREDENTIALS_JSON'):
    cred_dict = json.loads(os.getenv('FIREBASE_CREDENTIALS_JSON'))
    cred = credentials.Certificate(cred_dict)
else:
    cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', './firebase-credentials.json')
    cred = credentials.Certificate(cred_path)
```

#### Опциональные:
```
ADMIN_USER_IDS=123456789,987654321
LOGIST_USER_IDS=111222333
OPERATOR_USER_IDS=444555666
SCHEDULE_MOVE_TO_TODAY=07:30
SCHEDULE_MORNING_REPORT=09:00
SCHEDULE_DAY_REPORT=20:00
SCHEDULE_SLA_CHECK=*/10
SLA_NO_ANSWER_RETRY=30
SLA_BAD_NUMBER_ESCALATION=60
```

### Шаг 4: Запустите деплой

1. Нажмите **"Create Background Worker"**
2. Render начнет сборку и деплой
3. Следите за логами в разделе **"Logs"**

## Обновление кода

После каждого изменения в коде:

```bash
git add .
git commit -m "Описание изменений"
git push origin main
```

Render автоматически перезапустит сервис при новом коммите.

## Мониторинг

- **Logs:** Просматривайте логи в реальном времени в Render Dashboard
- **Metrics:** Мониторинг использования ресурсов
- **Events:** История деплоев и событий

## Устранение проблем

### Бот не запускается

1. Проверьте логи в Render Dashboard
2. Убедитесь, что все переменные окружения установлены
3. Проверьте формат Firebase credentials JSON

### Ошибка импорта модулей

Убедитесь, что `src/__init__.py` существует и структура проекта правильная.

### Firebase credentials не работают

Проверьте, что JSON правильно экранирован в переменной окружения `FIREBASE_CREDENTIALS_JSON`.

## Альтернатива: Использование файла credentials

Если предпочитаете использовать файл:

1. Создайте секрет в Render: **"Secrets"** → **"Add Secret"**
2. Название: `FIREBASE_CREDENTIALS`
3. Значение: содержимое `firebase-credentials.json`
4. В коде создайте файл из секрета при запуске

## Стоимость

Render предоставляет бесплатный план для Background Workers:
- 750 часов в месяц бесплатно
- Автоматическое отключение после 15 минут бездействия (можно включить "Always On" за $7/месяц)

## Полезные ссылки

- [Render Documentation](https://render.com/docs)
- [Python Background Workers](https://render.com/docs/background-workers)
- [Environment Variables](https://render.com/docs/environment-variables)

