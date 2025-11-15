"""Утилиты для создания клавиатур"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from typing import Dict, Any, Optional, List
from src.config import WEB_APP_URL


def get_order_keyboard(order: Dict[str, Any], user_role: str) -> InlineKeyboardMarkup:
    """Получить клавиатуру для карточки заказа"""
    status = order.get('status', 'NEW')
    order_id = order.get('id', '')
    
    buttons = []
    
    # Кнопки в зависимости от статуса и роли
    if status == 'PUBLISHED_TODAY' and user_role in ['courier', 'logist']:
        buttons.append([InlineKeyboardButton(
            text='✅ Взять',
            callback_data=f'order:take:{order_id}'
        )])
    
    if status == 'ASSIGNED' and user_role in ['courier', 'logist']:
        buttons.append([InlineKeyboardButton(
            text='📞 Позвонил',
            callback_data=f'order:call_menu:{order_id}'
        )])
    
    if status == 'CONFIRMED' and user_role in ['courier', 'logist']:
        buttons.append([InlineKeyboardButton(
            text='🚗 В пути',
            callback_data=f'order:on_the_way:{order_id}'
        )])
    
    if status == 'ON_THE_WAY' and user_role in ['courier', 'logist']:
        buttons.append([
            InlineKeyboardButton(
                text='📦 Доставлено',
                callback_data=f'order:delivered:{order_id}'
            ),
            InlineKeyboardButton(
                text='🔄 Возврат',
                callback_data=f'order:return_menu:{order_id}'
            )
        ])
    
    # Общие кнопки
    buttons.append([
        InlineKeyboardButton(
            text='💬 Комментарий',
            callback_data=f'order:comment:{order_id}'
        ),
        InlineKeyboardButton(
            text='📋 Детали',
            callback_data=f'order:details:{order_id}'
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_call_status_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для статуса звонка"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text='✅ Подтвержден',
                callback_data=f'order:call:confirmed:{order_id}'
            )
        ],
        [
            InlineKeyboardButton(
                text='🔄 Перенести',
                callback_data=f'order:call:reschedule:{order_id}'
            ),
            InlineKeyboardButton(
                text='📞 Нет ответа',
                callback_data=f'order:call:no_answer:{order_id}'
            )
        ],
        [
            InlineKeyboardButton(
                text='❌ Неверный номер',
                callback_data=f'order:call:bad_number:{order_id}'
            ),
            InlineKeyboardButton(
                text='⚠️ Фейк',
                callback_data=f'order:call:fake:{order_id}'
            )
        ],
        [
            InlineKeyboardButton(
                text='🚫 Отказ',
                callback_data=f'order:call:declined:{order_id}'
            )
        ],
        [
            InlineKeyboardButton(
                text='◀️ Назад',
                callback_data=f'order:back:{order_id}'
            )
        ]
    ])


def get_return_type_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для типа возврата"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text='📦 Частичный возврат',
                callback_data=f'order:return:partial:{order_id}'
            )
        ],
        [
            InlineKeyboardButton(
                text='🔄 Полный возврат',
                callback_data=f'order:return:full:{order_id}'
            )
        ],
        [
            InlineKeyboardButton(
                text='◀️ Назад',
                callback_data=f'order:back:{order_id}'
            )
        ]
    ])


def get_reschedule_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для выбора новой даты"""
    from datetime import datetime, timedelta
    
    buttons = []
    today = datetime.now()
    
    # Предлагаем следующие 7 дней
    for i in range(1, 8):
        date = today + timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        date_display = date.strftime('%d.%m')
        day_name = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][date.weekday()]
        
        buttons.append([InlineKeyboardButton(
            text=f'{date_display} ({day_name})',
            callback_data=f'order:reschedule:{order_id}:{date_str}'
        )])
    
    buttons.append([
        InlineKeyboardButton(
            text='◀️ Назад',
            callback_data=f'order:back:{order_id}'
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_menu_keyboard(user_role: str) -> InlineKeyboardMarkup:
    """Главное меню в зависимости от роли"""
    buttons = []
    
    if user_role in ['operator', 'admin']:
        buttons.append([
            InlineKeyboardButton(
                text='➕ Создать заказ',
                web_app=WebAppInfo(url=f"{WEB_APP_URL}/orders/new")
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text='📋 Мои заказы', callback_data='menu:my_orders'),
        InlineKeyboardButton(text='📅 Сегодня', callback_data='menu:today')
    ])
    
    buttons.append([
        InlineKeyboardButton(text='📆 Завтра', callback_data='menu:tomorrow'),
        InlineKeyboardButton(text='⚡ Требуют действия', callback_data='menu:action')
    ])
    
    if user_role in ['logist', 'admin']:
        buttons.append([
            InlineKeyboardButton(text='📊 Отчеты', callback_data='menu:reports')
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_order_action_keyboard(order_id: str, user_role: str) -> InlineKeyboardMarkup:
    """Клавиатура для действий оператора с заказом"""
    buttons = []
    
    if user_role in ['operator', 'admin']:
        buttons.append([
            InlineKeyboardButton(
                text='📞 Перезвонить',
                callback_data=f'order:operator:recall:{order_id}'
            ),
            InlineKeyboardButton(
                text='✏️ Исправить номер',
                callback_data=f'order:operator:fix_number:{order_id}'
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text='✅ Подтвердить перенос',
                callback_data=f'order:operator:confirm_reschedule:{order_id}'
            ),
            InlineKeyboardButton(
                text='🚫 Закрыть с отказом',
                callback_data=f'order:operator:close_declined:{order_id}'
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text='◀️ Назад к списку',
            callback_data='menu:action'
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

