"""Обработчики команд бота"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.services.firebase import FirebaseService
from src.services.orders import OrderService
from src.utils.keyboards import get_main_menu_keyboard
from src.utils.formatters import format_order_list
from datetime import datetime

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, db_user: dict = None):
    """Обработчик команды /start"""
    user = db_user
    
    if not user:
        # Регистрация нового пользователя
        await message.answer(
            "👋 Добро пожаловать!\n\n"
            "Вы не зарегистрированы в системе. Обратитесь к администратору для получения доступа."
        )
        return
    
    role = user.get('role', 'operator')
    name = user.get('displayName', 'Пользователь')
    
    welcome_text = f"""👋 Привет, {name}!

Ваша роль: {role.upper()}

Используйте команды:
/new - создать заказ
/orders - мои заказы
/today - заказы на сегодня
/tomorrow - заказы на завтра
/action - требуют действия
"""
    
    if role in ['logist', 'admin']:
        welcome_text += "/report - отчеты\n"
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(role)
    )


@router.message(Command("new"))
async def cmd_new(message: Message, db_user: dict = None, user_role: str = None):
    """Создать новый заказ (открывает Web App)"""
    if not db_user:
        await message.answer("❌ Вы не авторизованы. Используйте /start")
        return
    
    if user_role not in ['operator', 'admin']:
        await message.answer("❌ У вас нет прав для создания заказов")
        return
    
    from src.config import WEB_APP_URL
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="➕ Создать заказ",
            web_app=WebAppInfo(url=f"{WEB_APP_URL}/orders/new")
        )
    ]])
    
    await message.answer(
        "📝 Создание нового заказа\n\n"
        "Нажмите кнопку ниже, чтобы открыть форму:",
        reply_markup=keyboard
    )


@router.message(Command("orders"))
async def cmd_orders(message: Message, db_user: dict = None, user_role: str = None):
    """Мои заказы"""
    if not db_user:
        await message.answer("❌ Вы не авторизованы")
        return
    
    user_id = db_user.get('id')
    orders = await OrderService.get_orders_for_user(user_id, user_role, 'all')
    
    if not orders:
        await message.answer("📋 У вас нет заказов")
        return
    
    text = format_order_list(orders[:10], "Мои заказы")
    await message.answer(text, parse_mode='Markdown')


@router.message(Command("today"))
async def cmd_today(message: Message, db_user: dict = None, user_role: str = None):
    """Заказы на сегодня"""
    if not db_user:
        await message.answer("❌ Вы не авторизованы")
        return
    
    user_id = db_user.get('id')
    orders = await OrderService.get_orders_for_user(user_id, user_role, 'today')
    
    if not orders:
        await message.answer("📅 Нет заказов на сегодня")
        return
    
    text = format_order_list(orders[:10], "Заказы на сегодня")
    await message.answer(text, parse_mode='Markdown')


@router.message(Command("tomorrow"))
async def cmd_tomorrow(message: Message, db_user: dict = None, user_role: str = None):
    """Заказы на завтра"""
    if not db_user:
        await message.answer("❌ Вы не авторизованы")
        return
    
    user_id = db_user.get('id')
    orders = await OrderService.get_orders_for_user(user_id, user_role, 'tomorrow')
    
    if not orders:
        await message.answer("📆 Нет заказов на завтра")
        return
    
    text = format_order_list(orders[:10], "Заказы на завтра")
    await message.answer(text, parse_mode='Markdown')


@router.message(Command("action"))
async def cmd_action(message: Message, db_user: dict = None, user_role: str = None):
    """Заказы, требующие действия"""
    if not db_user:
        await message.answer("❌ Вы не авторизованы")
        return
    
    if user_role not in ['operator', 'logist', 'admin']:
        await message.answer("❌ У вас нет прав для просмотра этого раздела")
        return
    
    user_id = db_user.get('id')
    orders = await OrderService.get_orders_for_user(user_id, user_role, 'action')
    
    if not orders:
        await message.answer("✅ Нет заказов, требующих действия")
        return
    
    text = format_order_list(orders[:10], "Требуют действия")
    await message.answer(text, parse_mode='Markdown')


@router.message(Command("report"))
async def cmd_report(message: Message, db_user: dict = None, user_role: str = None):
    """Отчеты (для логистов)"""
    if not db_user:
        await message.answer("❌ Вы не авторизованы")
        return
    
    if user_role not in ['logist', 'admin']:
        await message.answer("❌ У вас нет прав для просмотра отчетов")
        return
    
    from src.utils.formatters import format_report
    from datetime import datetime
    
    today = datetime.now().strftime('%Y-%m-%d')
    orders = FirebaseService.get_orders_by_date(today)
    
    # Подсчитываем по статусам
    statuses = {}
    for order in orders:
        status = order.get('status', 'NEW')
        statuses[status] = statuses.get(status, 0) + 1
    
    report_text = format_report(statuses, today)
    await message.answer(report_text, parse_mode='Markdown')


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Справка по командам"""
    help_text = """📖 *Справка по командам*

*/start* - Начать работу с ботом
*/new* - Создать новый заказ (Web App)
*/orders* - Мои заказы
*/today* - Заказы на сегодня
*/tomorrow* - Заказы на завтра
*/action* - Заказы, требующие действия
*/help* - Эта справка

*Для логистов и админов:*
*/report* - Отчеты

*Использование:*
- Нажимайте кнопки под карточками заказов для изменения статусов
- Все действия логируются в системе
"""
    await message.answer(help_text, parse_mode='Markdown')
