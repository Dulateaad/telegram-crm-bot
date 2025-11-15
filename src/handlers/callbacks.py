"""Обработчики callback кнопок"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from src.services.orders import OrderService
from src.services.notifications import NotificationService
from src.services.firebase import FirebaseService
from src.utils.keyboards import (
    get_call_status_keyboard,
    get_return_type_keyboard,
    get_reschedule_keyboard,
    get_order_keyboard,
    get_order_action_keyboard
)
from src.utils.formatters import format_order_card
from datetime import datetime

router = Router()


@router.callback_query(F.data.startswith("order:take:"))
async def callback_take_order(callback: CallbackQuery, db_user: dict = None, user_role: str = None):
    """Взять заказ"""
    if not db_user or user_role not in ['courier', 'logist', 'admin']:
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    order_id = callback.data.split(":")[-1]
    user_id = db_user.get('id')
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status='ASSIGNED',
        user_id=user_id,
        user_role=user_role
    )
    
    if result.get('success'):
        await callback.answer("✅ Заказ взят в работу")
        
        # Обновляем карточку в чате
        order = result.get('order')
        if order:
            # TODO: Обновить сообщение в региональном чате
            await callback.message.edit_text(
                format_order_card(order),
                parse_mode='Markdown',
                reply_markup=get_order_keyboard(order, user_role)
            )
    else:
        await callback.answer("❌ Ошибка при взятии заказа", show_alert=True)


@router.callback_query(F.data.startswith("order:call_menu:"))
async def callback_call_menu(callback: CallbackQuery):
    """Меню статусов звонка"""
    order_id = callback.data.split(":")[-1]
    
    await callback.message.edit_reply_markup(
        reply_markup=get_call_status_keyboard(order_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order:call:confirmed:"))
async def callback_call_confirmed(callback: CallbackQuery, db_user: dict = None, user_role: str = None):
    """Звонок: подтвержден"""
    order_id = callback.data.split(":")[-1]
    user_id = db_user.get('id') if db_user else 'system'
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status='CONFIRMED',
        user_id=user_id,
        user_role=user_role or 'courier',
        note='Клиент подтвердил заказ'
    )
    
    if result.get('success'):
        await callback.answer("✅ Заказ подтвержден")
        order = result.get('order')
        if order:
            await callback.message.edit_text(
                format_order_card(order),
                parse_mode='Markdown',
                reply_markup=get_order_keyboard(order, user_role or 'courier')
            )
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("order:call:no_answer:"))
async def callback_call_no_answer(callback: CallbackQuery, db_user: dict = None, user_role: str = None):
    """Звонок: нет ответа"""
    order_id = callback.data.split(":")[-1]
    user_id = db_user.get('id') if db_user else 'system'
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status='NO_ANSWER',
        user_id=user_id,
        user_role=user_role or 'courier',
        reason_code='NO_ANSWER',
        note='Клиент не отвечает на звонок'
    )
    
    if result.get('success'):
        await callback.answer("📞 Статус: нет ответа")
        # TODO: Создать задачу оператору на повторный звонок через SLA
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("order:call:bad_number:"))
async def callback_call_bad_number(callback: CallbackQuery, db_user: dict = None, user_role: str = None):
    """Звонок: неверный номер"""
    order_id = callback.data.split(":")[-1]
    user_id = db_user.get('id') if db_user else 'system'
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status='BAD_NUMBER',
        user_id=user_id,
        user_role=user_role or 'courier',
        reason_code='BAD_NUMBER',
        note='Неверный номер телефона'
    )
    
    if result.get('success'):
        await callback.answer("❌ Статус: неверный номер")
        # TODO: Создать задачу оператору на проверку номера
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("order:call:fake:"))
async def callback_call_fake(callback: CallbackQuery, db_user: dict = None, user_role: str = None):
    """Звонок: фейк"""
    order_id = callback.data.split(":")[-1]
    user_id = db_user.get('id') if db_user else 'system'
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status='FAKE',
        user_id=user_id,
        user_role=user_role or 'courier',
        reason_code='FAKE',
        note='Фейковый заказ'
    )
    
    if result.get('success'):
        await callback.answer("⚠️ Статус: фейк")
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("order:call:declined:"))
async def callback_call_declined(callback: CallbackQuery, db_user: dict = None, user_role: str = None):
    """Звонок: отказ"""
    order_id = callback.data.split(":")[-1]
    user_id = db_user.get('id') if db_user else 'system'
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status='DECLINED',
        user_id=user_id,
        user_role=user_role or 'courier',
        reason_code='DECLINED',
        note='Клиент отказался от заказа'
    )
    
    if result.get('success'):
        await callback.answer("🚫 Статус: отказ")
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("order:call:reschedule:"))
async def callback_call_reschedule_menu(callback: CallbackQuery):
    """Меню переноса даты"""
    order_id = callback.data.split(":")[-1]
    
    await callback.message.edit_reply_markup(
        reply_markup=get_reschedule_keyboard(order_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order:reschedule:"))
async def callback_reschedule(callback: CallbackQuery, db_user: dict = None, user_role: str = None):
    """Перенести заказ на другую дату"""
    parts = callback.data.split(":")
    order_id = parts[2]
    new_date = parts[3]
    user_id = db_user.get('id') if db_user else 'system'
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status='RESCHEDULED',
        user_id=user_id,
        user_role=user_role or 'courier',
        reason_code='RESCHEDULED',
        note=f'Заказ перенесен на {new_date}'
    )
    
    if result.get('success'):
        # TODO: Обновить deliveryDate в заказе
        await callback.answer(f"🔄 Заказ перенесен на {new_date}")
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("order:on_the_way:"))
async def callback_on_the_way(callback: CallbackQuery, db_user: dict = None, user_role: str = None):
    """В пути"""
    order_id = callback.data.split(":")[-1]
    user_id = db_user.get('id') if db_user else 'system'
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status='ON_THE_WAY',
        user_id=user_id,
        user_role=user_role or 'courier',
        note='Курьер в пути к клиенту'
    )
    
    if result.get('success'):
        await callback.answer("🚗 Статус: в пути")
        order = result.get('order')
        if order:
            await callback.message.edit_text(
                format_order_card(order),
                parse_mode='Markdown',
                reply_markup=get_order_keyboard(order, user_role or 'courier')
            )
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("order:delivered:"))
async def callback_delivered(callback: CallbackQuery, db_user: dict = None, user_role: str = None):
    """Доставлено"""
    order_id = callback.data.split(":")[-1]
    user_id = db_user.get('id') if db_user else 'system'
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status='DELIVERED',
        user_id=user_id,
        user_role=user_role or 'courier',
        note='Заказ доставлен'
    )
    
    if result.get('success'):
        await callback.answer("📦 Заказ доставлен!")
        order = result.get('order')
        if order:
            await callback.message.edit_text(
                format_order_card(order),
                parse_mode='Markdown',
                reply_markup=get_order_keyboard(order, user_role or 'courier')
            )
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("order:return_menu:"))
async def callback_return_menu(callback: CallbackQuery):
    """Меню возврата"""
    order_id = callback.data.split(":")[-1]
    
    await callback.message.edit_reply_markup(
        reply_markup=get_return_type_keyboard(order_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order:return:partial:"))
async def callback_return_partial(callback: CallbackQuery, db_user: dict = None, user_role: str = None):
    """Частичный возврат"""
    order_id = callback.data.split(":")[-1]
    user_id = db_user.get('id') if db_user else 'system'
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status='PARTIAL_RETURN',
        user_id=user_id,
        user_role=user_role or 'courier',
        reason_code='PARTIAL_RETURN',
        note='Частичный возврат товара'
    )
    
    if result.get('success'):
        await callback.answer("🔄 Частичный возврат")
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("order:return:full:"))
async def callback_return_full(callback: CallbackQuery, db_user: dict = None, user_role: str = None):
    """Полный возврат"""
    order_id = callback.data.split(":")[-1]
    user_id = db_user.get('id') if db_user else 'system'
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status='FULL_RETURN',
        user_id=user_id,
        user_role=user_role or 'courier',
        reason_code='FULL_RETURN',
        note='Полный возврат товара'
    )
    
    if result.get('success'):
        await callback.answer("🔄 Полный возврат")
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("order:comment:"))
async def callback_comment(callback: CallbackQuery, state: FSMContext):
    """Добавить комментарий"""
    order_id = callback.data.split(":")[-1]
    
    await state.update_data(order_id=order_id)
    await callback.message.answer("💬 Введите комментарий к заказу:")
    # TODO: Настроить FSM состояния
    # await state.set_state("waiting_comment")
    await callback.answer()


@router.callback_query(F.data.startswith("order:details:"))
async def callback_order_details(callback: CallbackQuery):
    """Детали заказа"""
    order_id = callback.data.split(":")[-1]
    
    order = FirebaseService.get_order(order_id)
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    # Показываем полную информацию
    details = format_order_card(order, show_buttons=False)
    
    # Добавляем историю
    history = order.get('history', [])
    if history:
        details += "\n\n*История изменений:*\n"
        for event in history[-5:]:  # Последние 5 событий
            details += f"• {event.get('to')} - {event.get('note', '')}\n"
    
    await callback.message.answer(details, parse_mode='Markdown')
    await callback.answer()


@router.callback_query(F.data.startswith("menu:"))
async def callback_menu(callback: CallbackQuery, db_user: dict = None, user_role: str = None):
    """Обработка меню"""
    if not db_user:
        await callback.answer("❌ Вы не авторизованы", show_alert=True)
        return
    
    menu_action = callback.data.split(":")[-1]
    user_id = db_user.get('id')
    
    if menu_action == "my_orders":
        orders = await OrderService.get_orders_for_user(user_id, user_role, 'all')
        from src.utils.formatters import format_order_list
        text = format_order_list(orders[:10], "Мои заказы")
        await callback.message.answer(text, parse_mode='Markdown')
        await callback.answer()
    
    elif menu_action == "today":
        orders = await OrderService.get_orders_for_user(user_id, user_role, 'today')
        from src.utils.formatters import format_order_list
        text = format_order_list(orders[:10], "Заказы на сегодня")
        await callback.message.answer(text, parse_mode='Markdown')
        await callback.answer()
    
    elif menu_action == "tomorrow":
        orders = await OrderService.get_orders_for_user(user_id, user_role, 'tomorrow')
        from src.utils.formatters import format_order_list
        text = format_order_list(orders[:10], "Заказы на завтра")
        await callback.message.answer(text, parse_mode='Markdown')
        await callback.answer()
    
    elif menu_action == "action":
        if user_role not in ['operator', 'logist', 'admin']:
            await callback.answer("❌ У вас нет прав", show_alert=True)
            return
        
        orders = await OrderService.get_orders_for_user(user_id, user_role, 'action')
        from src.utils.formatters import format_order_list
        text = format_order_list(orders[:10], "Требуют действия")
        await callback.message.answer(text, parse_mode='Markdown')
        await callback.answer()
    
    elif menu_action == "reports":
        if user_role not in ['logist', 'admin']:
            await callback.answer("❌ У вас нет прав", show_alert=True)
            return
        
        await callback.message.answer("📊 Отчеты доступны по команде /report")
        await callback.answer()

