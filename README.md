# Telegram CRM Bot для управления заказами

Telegram бот для управления заказами доставки с интеграцией Firebase Firestore и React Mini App.

## Архитектура

- **Telegram Bot** (Python + aiogram 3.x) - обработка команд, кнопок, уведомлений
- **Firebase Firestore** - база данных
- **React Mini App** - формы для операторов (в репозитории CRM)
- **APScheduler** - автоматические задачи (перекат заказов, отчеты)

## Установка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Заполните .env файл

# Настройка Firebase Admin SDK
# Скачайте credentials.json из Firebase Console
# Service Account → Generate new private key
# Сохраните как firebase-credentials.json

# Запуск бота
python src/main.py
```

## Структура проекта

```
telegram-bot-crm/
├── src/
│   ├── main.py                 # Точка входа
│   ├── bot.py                  # Инициализация бота
│   ├── config.py               # Конфигурация
│   ├── handlers/               # Обработчики команд и callback
│   │   ├── __init__.py
│   │   ├── commands.py         # Команды /start, /help, /new
│   │   ├── callbacks.py        # Обработка кнопок заказов
│   │   └── webapp.py           # Интеграция с Web App
│   ├── middleware/             # Middleware
│   │   ├── __init__.py
│   │   ├── auth.py             # Проверка ролей
│   │   └── logging.py          # Логирование
│   ├── services/               # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── firebase.py         # Работа с Firestore
│   │   ├── orders.py           # Управление заказами
│   │   ├── notifications.py   # Отправка уведомлений
│   │   ├── reports.py          # Генерация отчетов
│   │   └── scheduler.py        # Планировщик задач
│   └── utils/                  # Утилиты
│       ├── __init__.py
│       ├── keyboards.py        # Клавиатуры бота
│       ├── formatters.py       # Форматирование сообщений
│       └── validators.py       # Валидация данных
├── requirements.txt
├── .env.example
└── README.md
```

## Функционал

### Роли пользователей
- **operator** - создание заказов, обработка обратной связи
- **logist** - распределение заказов, отчеты
- **courier** - выполнение заказов, обновление статусов
- **admin** - полный доступ

### Основные функции
1. Создание заказов через Web App форму
2. Автораспределение по дате и региону
3. Карточки заказов в региональных чатах
4. Обновление статусов через кнопки
5. Обратная связь для операторов
6. Автоматические отчеты (09:00, 20:00)
7. SLA контроль и эскалации

## Команды бота

- `/start` - регистрация/авторизация
- `/new` - создать новый заказ (открывает Web App)
- `/orders` - мои заказы
- `/today` - заказы на сегодня
- `/tomorrow` - заказы на завтра
- `/action` - заказы, требующие действия
- `/report` - отчеты (для логистов)

## Развертывание

### Локально
```bash
python src/main.py
```

### На сервере (systemd)
Создайте файл `/etc/systemd/system/telegram-crm-bot.service`:

```ini
[Unit]
Description=Telegram CRM Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/telegram-bot-crm
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python src/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable telegram-crm-bot
sudo systemctl start telegram-crm-bot
```

## Интеграция с React Mini App

Бот отправляет кнопку с Web App для создания заказов:
```python
web_app = WebAppInfo(url="https://your-mini-app-url.com/new-order")
keyboard = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="Создать заказ", web_app=web_app)
]])
```

Mini App отправляет данные обратно через `window.Telegram.WebApp.sendData()`.

