# Интеграция Telegram бота с React Mini App

## Настройка Web App в React Mini App

### 1. Обновление формы создания заказа

В файле `src/components/app/order-form.tsx` добавьте отправку данных в Telegram:

```typescript
import { useTelegram } from '@/hooks/use-telegram';

export function OrderForm() {
  const { webApp } = useTelegram();
  
  const handleSubmit = async (formData: FormData) => {
    // ... валидация и создание заказа ...
    
    // После успешного создания заказа отправляем данные в бот
    if (webApp) {
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
        deliveryDate: formData.get('deliveryDate') === 'today' 
          ? new Date().toISOString().split('T')[0]
          : new Date(Date.now() + 86400000).toISOString().split('T')[0],
        timeWindowFrom: formData.get('timeWindowFrom'),
        timeWindowTo: formData.get('timeWindowTo'),
        regionId: formData.get('regionId'),
        comment: formData.get('comment'),
      };
      
      // Отправляем данные в Telegram бот
      webApp.sendData(JSON.stringify(orderData));
      
      // Закрываем Web App
      webApp.close();
    }
  };
}
```

### 2. Настройка Web App URL в боте

В `.env` файле бота укажите URL вашего React Mini App:

```env
WEB_APP_URL=https://your-mini-app-url.com
```

### 3. Настройка кнопки Web App в боте

Бот автоматически создает кнопку с Web App при команде `/new`. 

Для ручной настройки в `src/utils/keyboards.py`:

```python
from aiogram.types import WebAppInfo

web_app_button = InlineKeyboardButton(
    text="➕ Создать заказ",
    web_app=WebAppInfo(url=f"{WEB_APP_URL}/orders/new")
)
```

## Поток данных

1. **Пользователь нажимает кнопку "Создать заказ"** в боте
2. **Открывается Web App** с формой создания заказа
3. **Пользователь заполняет форму** и нажимает "Создать"
4. **React App отправляет данные** через `webApp.sendData()`
5. **Бот получает данные** в обработчике `handle_webapp_data`
6. **Бот создает заказ** в Firestore
7. **Бот отправляет заказ** в региональный чат
8. **Бот подтверждает** оператору успешное создание

## Структура данных Web App

```typescript
interface WebAppOrderData {
  customer: {
    name: string;
    phone: string; // формат: +998XXXXXXXXX
    address: string;
    landmarks?: string;
  };
  items: Array<{
    name: string;
    quantity: number;
    price?: number;
  }>;
  totalAmount: number;
  paymentType: 'CASH' | 'CARD' | 'TRANSFER';
  deliveryDate: string; // формат: YYYY-MM-DD
  timeWindowFrom: string; // формат: HH:mm
  timeWindowTo: string; // формат: HH:mm
  regionId: string;
  comment?: string;
}
```

## Обработка ошибок

Бот отправляет сообщения об ошибках обратно в Web App через Telegram:

- `❌ Ошибка: не указан телефон клиента`
- `❌ Ошибка: не выбран регион`
- `⚠️ Найден дубликат заказа`
- `✅ Заказ создан успешно!`

## Тестирование

1. Запустите React Mini App локально или на сервере
2. Убедитесь, что Web App доступен по HTTPS
3. Настройте Web App в BotFather:
   - `/newapp` - создать новое приложение
   - Укажите URL вашего Mini App
   - Получите Web App URL
4. Обновите `WEB_APP_URL` в `.env` бота
5. Перезапустите бота
6. Протестируйте создание заказа через `/new`

