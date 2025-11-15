"""Сервис для отправки уведомлений в Telegram"""
from aiogram import Bot
from aiogram.types import Message
from typing import Dict, Any, Optional
from datetime import datetime
from src.services.firebase import FirebaseService
from src.utils.formatters import format_order_card
from src.utils.keyboards import get_order_keyboard


class NotificationService:
    """Сервис для отправки уведомлений"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def send_order_to_region_chat(self, order: Dict[str, Any]) -> Optional[Message]:
        """Отправить заказ в региональный чат"""
        region = FirebaseService.get_region(order.get('regionId', ''))
        if not region:
            return None
        
        # Определяем топик в зависимости от статуса
        status = order.get('status', '')
        topic_id = None
        
        if status == 'PUBLISHED_TODAY':
            topic_id = region.get('topics', {}).get('todayTopicId')
        elif status == 'QUEUED_TOMORROW':
            topic_id = region.get('topics', {}).get('tomorrowQueueId')
        
        chat_id = region.get('telegramChatId')
        if not chat_id:
            return None
        
        # Форматируем карточку заказа
        card_text = format_order_card(order, show_buttons=True)
        keyboard = get_order_keyboard(order, 'courier')
        
        try:
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=card_text,
                parse_mode='Markdown',
                reply_markup=keyboard,
                message_thread_id=int(topic_id) if topic_id else None
            )
            return message
        except Exception as e:
            print(f"Error sending order to region chat: {e}")
            return None
    
    async def update_order_card_in_chat(
        self,
        order: Dict[str, Any],
        message_id: int,
        chat_id: str
    ) -> bool:
        """Обновить карточку заказа в чате"""
        card_text = format_order_card(order, show_buttons=True)
        keyboard = get_order_keyboard(order, 'courier')
        
        try:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=card_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            return True
        except Exception as e:
            print(f"Error updating order card: {e}")
            return False
    
    async def notify_operator_action_required(
        self,
        order: Dict[str, Any],
        operator_id: str
    ) -> bool:
        """Уведомить оператора о необходимости действия"""
        user = FirebaseService.get_user_by_telegram_id(int(operator_id))
        if not user or not user.get('telegramId'):
            return False
        
        telegram_id = int(user['telegramId'])
        
        message = f"""⚡ *Требуется действие*

{format_order_card(order, show_buttons=False)}

Статус: {order.get('status')}
"""
        
        try:
            from src.utils.keyboards import get_order_action_keyboard
            keyboard = get_order_action_keyboard(order.get('id'), user.get('role', 'operator'))
            
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            return True
        except Exception as e:
            print(f"Error notifying operator: {e}")
            return False
    
    async def send_daily_report(
        self,
        report_data: Dict[str, Any],
        user_ids: list
    ) -> int:
        """Отправить ежедневный отчет пользователям"""
        from src.utils.formatters import format_report
        
        date = datetime.now().strftime('%d.%m.%Y')
        report_text = format_report(report_data, date)
        
        sent_count = 0
        for user_id in user_ids:
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=report_text,
                    parse_mode='Markdown'
                )
                sent_count += 1
            except Exception as e:
                print(f"Error sending report to {user_id}: {e}")
        
        return sent_count

