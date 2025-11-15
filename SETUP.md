# Инструкция по настройке и запуску Telegram CRM бота

## Предварительные требования

1. Python 3.8+
2. Telegram Bot Token (получить у @BotFather)
3. Firebase Admin SDK credentials
4. Доступ к Firebase Firestore проекту

## Установка

### 1. Клонирование и установка зависимостей

```bash
cd telegram-bot-crm
pip install -r requirements.txt
```

### 2. Настройка Firebase Admin SDK

1. Откройте [Firebase Console](https://console.firebase.google.com/)
2. Выберите проект `studio-3898272712-a12a4`
3. Перейдите в **Project Settings** → **Service Accounts**
4. Нажмите **Generate new private key**
5. Сохраните JSON файл как `firebase-credentials.json` в корне проекта

### 3. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
nano .env
```

Обязательные переменные:

```env
# Telegram Bot Token (от @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Firebase
FIREBASE_PROJECT_ID=studio-3898272712-a12a4
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json

# Web App URL (React Mini App)
WEB_APP_URL=https://your-mini-app-url.com

# Telegram ID администраторов (через запятую)
ADMIN_USER_IDS=123456789,987654321

# Telegram ID логистов (опционально)
LOGIST_USER_IDS=111222333

# Telegram ID операторов (опционально)
OPERATOR_USER_IDS=444555666
```

### 4. Настройка регионов в Firestore

Создайте коллекцию `regions` в Firestore с такой структурой:

```javascript
{
  id: "region_1",
  name: "Ташкент",
  tz: "Asia/Tashkent",
  telegramChatId: "-1001234567890", // ID супергруппы
  topics: {
    todayTopicId: "123", // ID топика "Сегодня"
    tomorrowQueueId: "124" // ID топика "Завтра"
  }
}
```

### 5. Создание пользователей в Firestore

Создайте коллекцию `users` с пользователями:

```javascript
{
  id: "user_1",
  telegramId: "123456789", // Telegram User ID
  displayName: "Иван Иванов",
  role: "operator", // operator | logist | courier | admin
  regionId: "region_1",
  createdAt: Timestamp,
  updatedAt: Timestamp
}
```

## Запуск бота

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
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активируйте и запустите:

```bash
sudo systemctl enable telegram-crm-bot
sudo systemctl start telegram-crm-bot
sudo systemctl status telegram-crm-bot
```

## Интеграция с React Mini App

### 1. Обновите форму создания заказа

В `src/components/app/order-form.tsx` добавьте отправку данных в Telegram:

```typescript
import { useTelegram } from '@/hooks/use-telegram';

// В функции handleSubmit после успешного создания:
if (webApp && webApp.sendData) {
  const orderData = {
    customer: {
      name: formData.get('customerName'),
      phone: formData.get('phone'),
      address: formData.get('address'),
      landmarks: formData.get('landmarks'),
    },
    items: parseItems(formData.get('items')),
    totalAmount: parseFloat(formData.get('amount')),
    paymentType: formData.get('paymentType'),
    deliveryDate: deliveryDate === 'today' 
      ? new Date().toISOString().split('T')[0]
      : new Date(Date.now() + 86400000).toISOString().split('T')[0],
    timeWindowFrom: formData.get('timeWindowFrom'),
    timeWindowTo: formData.get('timeWindowTo'),
    regionId: formData.get('regionId'),
    comment: formData.get('comment'),
  };
  
  webApp.sendData(JSON.stringify(orderData));
  webApp.close();
}
```

### 2. Настройте Web App в BotFather

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newapp`
3. Выберите вашего бота
4. Укажите название и описание
5. Загрузите иконку (опционально)
6. Укажите URL вашего React Mini App: `https://your-mini-app-url.com`
7. Получите Web App URL

### 3. Обновите WEB_APP_URL в .env

```env
WEB_APP_URL=https://your-mini-app-url.com
```

## Тестирование

1. Запустите бота: `python src/main.py`
2. Откройте бота в Telegram
3. Отправьте `/start` - должно появиться приветствие
4. Отправьте `/new` - должна открыться форма Web App
5. Заполните форму и создайте заказ
6. Проверьте, что заказ появился в региональном чате

## Автоматические задачи

Бот автоматически выполняет:

- **07:30** - Перекат заказов "Завтра" → "Сегодня"
- **09:00** - Утренний отчет логистам
- **20:00** - Сводка дня
- **Каждые 10 минут** - Проверка SLA и эскалации

## Структура данных Firestore

### Коллекция `orders`

```javascript
{
  id: "order_123",
  idHuman: "#12345",
  status: "PUBLISHED_TODAY",
  customer: {
    name: "Азизбек",
    phone: "+998901234567",
    address: "ул. Навои, 15",
    landmarks: "Рядом с рынком"
  },
  items: [
    { name: "Хлеб", quantity: 2, price: 5000 },
    { name: "Молоко", quantity: 1, price: 12000 }
  ],
  totalAmount: 22000,
  paymentType: "CASH",
  deliveryDate: "2024-11-15",
  timeWindowFrom: "14:00",
  timeWindowTo: "18:00",
  regionId: "region_1",
  operatorId: "user_1",
  courierId: "user_2",
  comment: "Позвонить за час",
  history: [
    {
      by: "user_1",
      from: "NEW",
      to: "PUBLISHED_TODAY",
      at: "2024-11-15T10:00:00",
      note: "Заказ создан"
    }
  ],
  createdAt: Timestamp,
  updatedAt: Timestamp
}
```

### Коллекция `users`

```javascript
{
  id: "user_1",
  telegramId: "123456789",
  displayName: "Иван Иванов",
  role: "operator",
  regionId: "region_1",
  phone: "+998901234567",
  createdAt: Timestamp,
  updatedAt: Timestamp
}
```

### Коллекция `regions`

```javascript
{
  id: "region_1",
  name: "Ташкент",
  tz: "Asia/Tashkent",
  telegramChatId: "-1001234567890",
  topics: {
    todayTopicId: "123",
    tomorrowQueueId: "124"
  }
}
```

## Команды бота

- `/start` - Регистрация/авторизация
- `/new` - Создать заказ (открывает Web App)
- `/orders` - Мои заказы
- `/today` - Заказы на сегодня
- `/tomorrow` - Заказы на завтра
- `/action` - Заказы, требующие действия
- `/report` - Отчеты (для логистов)
- `/help` - Справка

## Устранение неполадок

### Бот не отвечает

1. Проверьте токен в `.env`
2. Проверьте логи: `tail -f bot.log`
3. Убедитесь, что бот запущен: `ps aux | grep python`

### Ошибки Firebase

1. Проверьте путь к credentials: `FIREBASE_CREDENTIALS_PATH`
2. Убедитесь, что файл существует и валиден
3. Проверьте права доступа к файлу

### Web App не открывается

1. Проверьте `WEB_APP_URL` в `.env`
2. Убедитесь, что URL доступен по HTTPS
3. Проверьте настройки Web App в BotFather

### Заказы не отправляются в чат

1. Проверьте `telegramChatId` в регионе
2. Убедитесь, что бот добавлен в супергруппу
3. Проверьте права бота (должен быть администратором)

## Поддержка

При возникновении проблем проверьте логи бота или создайте issue в репозитории.

