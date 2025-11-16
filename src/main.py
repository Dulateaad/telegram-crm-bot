#!/usr/bin/env python3
"""Главный файл для запуска бота"""
import asyncio
import logging
import sys
import os

# Добавляем корневую директорию проекта в путь для импортов
# Определяем корневую директорию проекта (на уровень выше src/)
current_file = os.path.abspath(__file__)
src_dir = os.path.dirname(current_file)
project_root = os.path.dirname(src_dir)

# Добавляем корневую директорию в начало пути
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Для отладки
print(f"🔍 Текущий файл: {current_file}")
print(f"🔍 Директория src: {src_dir}")
print(f"🔍 Корневая директория проекта: {project_root}")
print(f"🔍 PYTHONPATH: {sys.path[:3]}")

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

