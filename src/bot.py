"""Инициализация бота"""
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from src.config import TELEGRAM_BOT_TOKEN
from src.middleware import AuthMiddleware
from src.handlers import commands, callbacks, webapp
from src.services.scheduler import SchedulerService


def create_bot():
    """Создать и настроить бота"""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрируем middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    
    # Регистрируем роутеры
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(webapp.router)
    
    return bot, dp


async def start_bot():
    """Запустить бота"""
    bot, dp = create_bot()
    
    # Запускаем планировщик задач
    scheduler = SchedulerService(bot)
    scheduler.start()
    
    print("🤖 Бот запущен и готов к работе!")
    
    # Запускаем polling
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

