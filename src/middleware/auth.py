"""Middleware для проверки авторизации и ролей"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from src.services.firebase import FirebaseService


class AuthMiddleware(BaseMiddleware):
    """Middleware для проверки авторизации пользователя"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем пользователя из события
        user: User = data.get('event_from_user')
        if not user:
            return await handler(event, data)
        
        # Проверяем пользователя в базе
        db_user = FirebaseService.get_user_by_telegram_id(user.id)
        
        if not db_user:
            # Пользователь не найден - можно создать или отклонить
            # Пока просто пропускаем, обработчик сам решит что делать
            data['db_user'] = None
            data['user_role'] = None
        else:
            data['db_user'] = db_user
            data['user_role'] = db_user.get('role', 'operator')
        
        return await handler(event, data)

