#!/usr/bin/env python3
"""Главный файл для запуска бота"""
import asyncio
import logging
import sys
import os

# Добавляем корневую директорию проекта в путь для импортов
# Определяем корневую директорию проекта (на уровень выше src/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.bot import start_bot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Главная функция"""
    try:
        await start_bot()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)


if __name__ == '__main__':
    asyncio.run(main())

