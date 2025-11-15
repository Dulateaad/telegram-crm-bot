"""Планировщик автоматических задач"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from typing import Optional
from src.services.firebase import FirebaseService
from src.services.notifications import NotificationService
from src.config import (
    SCHEDULE_MOVE_TO_TODAY,
    SCHEDULE_MORNING_REPORT,
    SCHEDULE_DAY_REPORT,
    SCHEDULE_SLA_CHECK,
    SLA_NO_ANSWER_RETRY,
    SLA_BAD_NUMBER_ESCALATION
)
from aiogram import Bot


class SchedulerService:
    """Сервис для планирования задач"""
    
    def __init__(self, bot: Bot):
        self.scheduler = AsyncIOScheduler()
        self.bot = bot
        self.notification_service = NotificationService(bot)
    
    def start(self):
        """Запустить планировщик"""
        # Перекат заказов "Завтра" → "Сегодня" в 07:30
        hour, minute = SCHEDULE_MOVE_TO_TODAY.split(':')
        self.scheduler.add_job(
            self.move_tomorrow_to_today,
            trigger=CronTrigger(hour=int(hour), minute=int(minute)),
            id='move_tomorrow_to_today',
            name='Перекат заказов на сегодня'
        )
        
        # Утренний отчет в 09:00
        hour, minute = SCHEDULE_MORNING_REPORT.split(':')
        self.scheduler.add_job(
            self.send_morning_report,
            trigger=CronTrigger(hour=int(hour), minute=int(minute)),
            id='morning_report',
            name='Утренний отчет'
        )
        
        # Сводка дня в 20:00
        hour, minute = SCHEDULE_DAY_REPORT.split(':')
        self.scheduler.add_job(
            self.send_day_report,
            trigger=CronTrigger(hour=int(hour), minute=int(minute)),
            id='day_report',
            name='Сводка дня'
        )
        
        # Проверка SLA каждые 10 минут
        if SCHEDULE_SLA_CHECK.startswith('*/'):
            minutes = int(SCHEDULE_SLA_CHECK.split('/')[1])
            self.scheduler.add_job(
                self.check_sla,
                trigger=CronTrigger(minute=f'*/{minutes}'),
                id='sla_check',
                name='Проверка SLA'
            )
        
        self.scheduler.start()
        print("✅ Планировщик задач запущен")
    
    def stop(self):
        """Остановить планировщик"""
        self.scheduler.shutdown()
    
    async def move_tomorrow_to_today(self):
        """Перекатить заказы из очереди 'Завтра' в 'Сегодня'"""
        print(f"[{datetime.now()}] Перекат заказов на сегодня...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow_orders = FirebaseService.get_orders_by_status('QUEUED_TOMORROW')
        
        moved_count = 0
        for order in tomorrow_orders:
            # Проверяем, что дата доставки сегодня
            if order.get('deliveryDate') == today:
                # Обновляем статус
                FirebaseService.update_order_status(
                    order_id=order.get('id'),
                    new_status='PUBLISHED_TODAY',
                    user_id='system',
                    note='Автоматический перекат на сегодня'
                )
                
                # Отправляем в региональный чат
                updated_order = FirebaseService.get_order(order.get('id'))
                if updated_order:
                    await self.notification_service.send_order_to_region_chat(updated_order)
                
                moved_count += 1
        
        print(f"✅ Перекачено заказов: {moved_count}")
    
    async def send_morning_report(self):
        """Отправить утренний отчет логистам"""
        print(f"[{datetime.now()}] Отправка утреннего отчета...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        orders = FirebaseService.get_orders_by_date(today)
        
        # Подсчитываем по статусам
        statuses = {}
        for order in orders:
            status = order.get('status', 'NEW')
            statuses[status] = statuses.get(status, 0) + 1
        
        # Получаем всех логистов
        from src.config import LOGIST_USER_IDS, ADMIN_USER_IDS
        user_ids = LOGIST_USER_IDS + ADMIN_USER_IDS
        
        if user_ids:
            from src.utils.formatters import format_report
            report_text = format_report(statuses, today)
            
            sent = await self.notification_service.send_daily_report(statuses, user_ids)
            print(f"✅ Отправлено отчетов: {sent}")
    
    async def send_day_report(self):
        """Отправить сводку дня"""
        print(f"[{datetime.now()}] Отправка сводки дня...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        orders = FirebaseService.get_orders_by_date(today)
        
        # Подсчитываем по статусам
        statuses = {}
        total_amount = 0
        delivered_amount = 0
        
        for order in orders:
            status = order.get('status', 'NEW')
            statuses[status] = statuses.get(status, 0) + 1
            
            amount = order.get('totalAmount', 0)
            total_amount += amount
            if status == 'DELIVERED':
                delivered_amount += amount
        
        # Формируем расширенный отчет
        report = f"""*Сводка дня за {today}*

*Всего заказов:* {len(orders)}
*Сумма всех заказов:* {total_amount:,.0f} сум
*Сумма доставленных:* {delivered_amount:,.0f} сум

*По статусам:*
✅ Подтверждено: {statuses.get('CONFIRMED', 0)}
🚗 В пути: {statuses.get('ON_THE_WAY', 0)}
📦 Доставлено: {statuses.get('DELIVERED', 0)}
📞 Нет ответа: {statuses.get('NO_ANSWER', 0)}
❌ Плохой номер: {statuses.get('BAD_NUMBER', 0)}
⚠️ Фейк: {statuses.get('FAKE', 0)}
🚫 Отказ: {statuses.get('DECLINED', 0)}
🔄 Возврат: {statuses.get('PARTIAL_RETURN', 0) + statuses.get('FULL_RETURN', 0)}

*Конверсия:* {len([o for o in orders if o.get('status') == 'DELIVERED']) / len(orders) * 100:.1f}%
"""
        
        # Отправляем логистам и админам
        from src.config import LOGIST_USER_IDS, ADMIN_USER_IDS
        user_ids = LOGIST_USER_IDS + ADMIN_USER_IDS
        
        for user_id in user_ids:
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=report,
                    parse_mode='Markdown'
                )
            except Exception as e:
                print(f"Error sending report to {user_id}: {e}")
        
        print(f"✅ Сводка дня отправлена")
    
    async def check_sla(self):
        """Проверка SLA и создание задач"""
        print(f"[{datetime.now()}] Проверка SLA...")
        
        # Проверяем заказы с NO_ANSWER
        no_answer_orders = FirebaseService.get_orders_by_status('NO_ANSWER')
        
        for order in no_answer_orders:
            # Находим последнее событие NO_ANSWER
            history = order.get('history', [])
            last_no_answer = None
            
            for event in reversed(history):
                if event.get('to') == 'NO_ANSWER':
                    last_no_answer = event
                    break
            
            if last_no_answer:
                event_time = datetime.fromisoformat(last_no_answer.get('at', ''))
                minutes_passed = (datetime.now() - event_time).total_seconds() / 60
                
                # Если прошло больше SLA времени - создаем задачу оператору
                if minutes_passed >= SLA_NO_ANSWER_RETRY:
                    operator_id = order.get('operatorId')
                    if operator_id:
                        # TODO: Создать задачу в Firestore
                        print(f"⚠️ SLA нарушен для заказа {order.get('id')}: NO_ANSWER > {SLA_NO_ANSWER_RETRY} мин")
        
        # Проверяем заказы с BAD_NUMBER
        bad_number_orders = FirebaseService.get_orders_by_status('BAD_NUMBER')
        
        for order in bad_number_orders:
            history = order.get('history', [])
            last_bad_number = None
            
            for event in reversed(history):
                if event.get('to') == 'BAD_NUMBER':
                    last_bad_number = event
                    break
            
            if last_bad_number:
                event_time = datetime.fromisoformat(last_bad_number.get('at', ''))
                minutes_passed = (datetime.now() - event_time).total_seconds() / 60
                
                if minutes_passed >= SLA_BAD_NUMBER_ESCALATION:
                    operator_id = order.get('operatorId')
                    if operator_id:
                        # TODO: Эскалировать супервайзеру
                        print(f"⚠️ Эскалация для заказа {order.get('id')}: BAD_NUMBER > {SLA_BAD_NUMBER_ESCALATION} мин")

