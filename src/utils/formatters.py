"""Утилиты для форматирования сообщений"""
from typing import Dict, Any, Optional
from datetime import datetime
import re


def format_order_card(order: Dict[str, Any], show_buttons: bool = True) -> str:
    """Форматировать карточку заказа для Telegram"""
    customer = order.get('customer', {})
    items = order.get('items', [])
    
    # Форматирование даты
    delivery_date = order.get('deliveryDate', '')
    try:
        date_obj = datetime.strptime(delivery_date, '%Y-%m-%d')
        date_str = date_obj.strftime('%d.%m.%Y')
    except:
        date_str = delivery_date
    
    # Форматирование времени
    time_from = order.get('timeWindowFrom', '')
    time_to = order.get('timeWindowTo', '')
    time_window = f"{time_from}-{time_to}" if time_from and time_to else ""
    
    # Форматирование товаров
    items_text = []
    for item in items:
        name = item.get('name', '')
        qty = item.get('quantity', 1)
        items_text.append(f"{name} (x{qty})")
    items_str = ', '.join(items_text) if items_text else 'Нет товаров'
    
    # Форматирование суммы
    total_amount = order.get('totalAmount', 0)
    payment_type = order.get('paymentType', 'CASH')
    payment_type_ru = {
        'CASH': 'наличными',
        'CARD': 'картой',
        'TRANSFER': 'переводом'
    }.get(payment_type, payment_type)
    
    # Статус на русском
    status_ru = {
        'NEW': 'Новый',
        'QUEUED_TOMORROW': 'В очереди на завтра',
        'PUBLISHED_TODAY': 'Опубликован сегодня',
        'ASSIGNED': 'Назначен курьеру',
        'CONFIRMED': 'Подтвержден',
        'ON_THE_WAY': 'В пути',
        'DELIVERED': 'Доставлен',
        'PARTIAL_RETURN': 'Частичный возврат',
        'FULL_RETURN': 'Полный возврат',
        'RESCHEDULED': 'Перенесен',
        'NO_ANSWER': 'Нет ответа',
        'BAD_NUMBER': 'Неверный номер',
        'FAKE': 'Фейк',
        'DECLINED': 'Отказ'
    }.get(order.get('status', 'NEW'), order.get('status', 'NEW'))
    
    # Телефон с маскировкой
    phone = customer.get('phone', '')
    masked_phone = mask_phone(phone)
    
    # Формируем сообщение
    message = f"""*Заказ {order.get('idHuman', order.get('id', ''))}*

*Регион:* {order.get('regionName', order.get('regionId', ''))}
*Дата доставки:* {date_str}, {time_window}

*Клиент:* {customer.get('name', 'Не указано')}
*Телефон:* `{masked_phone}`
*Адрес:* {customer.get('address', 'Не указано')}
{f"*Ориентиры:* {customer.get('landmarks', '')}" if customer.get('landmarks') else ""}

*Состав заказа:* {items_str}
*Сумма:* {format_currency(total_amount)} ({payment_type_ru})
*Статус:* {status_ru}
"""
    
    if order.get('comment'):
        message += f"\n*Комментарий:* {order.get('comment')}"
    
    if order.get('courierName'):
        message += f"\n*Курьер:* {order.get('courierName')}"
    
    return message.strip()


def mask_phone(phone: str) -> str:
    """Замаскировать телефон для отображения"""
    if not phone:
        return 'Не указан'
    
    # Убираем все нецифровые символы кроме +
    digits = re.sub(r'[^\d+]', '', phone)
    
    if len(digits) >= 7:
        # Показываем первые 3 и последние 2 цифры
        return f"{digits[:3]}***{digits[-2:]}"
    
    return phone


def format_currency(amount: float) -> str:
    """Форматировать сумму валюты"""
    return f"{amount:,.0f} сум".replace(',', ' ')


def format_order_list(orders: list, title: str = "Заказы") -> str:
    """Форматировать список заказов"""
    if not orders:
        return f"*{title}*\n\nНет заказов"
    
    lines = [f"*{title}*", ""]
    
    for order in orders[:20]:  # Ограничиваем 20 заказами
        order_id = order.get('idHuman', order.get('id', ''))
        customer_name = order.get('customer', {}).get('name', 'Неизвестно')
        status = order.get('status', 'NEW')
        status_ru = {
            'NEW': '🆕',
            'ASSIGNED': '👤',
            'CONFIRMED': '✅',
            'ON_THE_WAY': '🚗',
            'DELIVERED': '📦',
            'NO_ANSWER': '📞',
            'BAD_NUMBER': '❌',
            'FAKE': '⚠️',
            'DECLINED': '🚫',
        }.get(status, '📋')
        
        lines.append(f"{status_ru} {order_id} - {customer_name} ({status})")
    
    if len(orders) > 20:
        lines.append(f"\n... и еще {len(orders) - 20} заказов")
    
    return '\n'.join(lines)


def format_report(orders_by_status: Dict[str, int], date: str) -> str:
    """Форматировать отчет"""
    total = sum(orders_by_status.values())
    
    report = f"""*Отчет за {date}*

*Всего заказов:* {total}

*По статусам:*
✅ Подтверждено: {orders_by_status.get('CONFIRMED', 0)}
🚗 В пути: {orders_by_status.get('ON_THE_WAY', 0)}
📦 Доставлено: {orders_by_status.get('DELIVERED', 0)}
📞 Нет ответа: {orders_by_status.get('NO_ANSWER', 0)}
❌ Плохой номер: {orders_by_status.get('BAD_NUMBER', 0)}
⚠️ Фейк: {orders_by_status.get('FAKE', 0)}
🚫 Отказ: {orders_by_status.get('DECLINED', 0)}
🔄 Возврат: {orders_by_status.get('PARTIAL_RETURN', 0) + orders_by_status.get('FULL_RETURN', 0)}
"""
    
    return report.strip()

