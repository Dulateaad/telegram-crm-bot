"""Обработчики данных из Web App"""
from aiogram import Router, F
from aiogram.types import Message, WebAppData
from aiogram.filters import ContentTypesFilter
import json
from src.services.orders import OrderService
from src.services.notifications import NotificationService
from src.services.firebase import FirebaseService
from src.utils.formatters import format_order_card
from src.utils.keyboards import get_order_keyboard
from datetime import datetime

router = Router()


@router.message(ContentTypesFilter(content_types=['web_app_data']))
async def handle_webapp_data(message: Message, db_user: dict = None, user_role: str = None, bot=None):
    """Обработка данных из Web App"""
    if not db_user:
        await message.answer("❌ Вы не авторизованы")
        return
    
    if user_role not in ['operator', 'admin']:
        await message.answer("❌ У вас нет прав для создания заказов")
        return
    
    try:
        # Парсим данные из Web App
        data = json.loads(message.web_app_data.data)
        
        # Валидация данных
        if not data.get('customer') or not data.get('customer', {}).get('phone'):
            await message.answer("❌ Ошибка: не указан телефон клиента")
            return
        
        if not data.get('regionId'):
            await message.answer("❌ Ошибка: не выбран регион")
            return
        
        # Создаем заказ
        operator_id = db_user.get('id')
        result = await OrderService.create_order_from_webapp(data, operator_id)
        
        if not result.get('success'):
            error_msg = result.get('message', 'Неизвестная ошибка')
            if result.get('error') == 'duplicate':
                await message.answer(
                    f"⚠️ {error_msg}\n\n"
                    "Проверьте, не создан ли уже заказ на этот номер и дату."
                )
            else:
                await message.answer(f"❌ Ошибка создания заказа: {error_msg}")
            return
        
        order = result.get('order')
        order_id = result.get('order_id')
        
        # Отправляем подтверждение оператору
        card_text = format_order_card(order, show_buttons=False)
        await message.answer(
            f"✅ *Заказ создан успешно!*\n\n{card_text}",
            parse_mode='Markdown'
        )
        
        # Отправляем заказ в региональный чат
        # Получаем bot из message.bot
        try:
            notification_service = NotificationService(message.bot)
            await notification_service.send_order_to_region_chat(order)
        except Exception as e:
            print(f"Error sending order to region chat: {e}")
        
        # Проверяем на дубликаты (предупреждение)
        duplicate = FirebaseService.check_duplicate_order(
            data.get('customer', {}).get('phone'),
            data.get('deliveryDate', '')
        )
        
        if duplicate and duplicate.get('id') != order_id:
            await message.answer(
                "⚠️ *Внимание:* Найден похожий заказ на этот номер и дату.\n"
                "Проверьте, не является ли это дубликатом.",
                parse_mode='Markdown'
            )
    
    except json.JSONDecodeError:
        await message.answer("❌ Ошибка: неверный формат данных")
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке данных: {str(e)}")
        print(f"Error handling webapp data: {e}")

