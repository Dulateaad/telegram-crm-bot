"""Сервис для управления заказами"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from src.services.firebase import FirebaseService
from src.utils.formatters import format_order_card
from src.utils.keyboards import get_order_keyboard


class OrderService:
    """Сервис для работы с заказами"""
    
    @staticmethod
    async def create_order_from_webapp(data: Dict[str, Any], operator_id: str) -> Dict[str, Any]:
        """Создать заказ из данных Web App"""
        # Проверка на дубликат
        phone = data.get('customer', {}).get('phone', '')
        delivery_date = data.get('deliveryDate', '')
        
        duplicate = FirebaseService.check_duplicate_order(phone, delivery_date)
        if duplicate:
            return {
                'success': False,
                'error': 'duplicate',
                'message': f'Найден дубликат заказа: {duplicate.get("idHuman", duplicate.get("id"))}'
            }
        
        # Определяем статус
        today = datetime.now().strftime('%Y-%m-%d')
        if delivery_date == today:
            status = 'PUBLISHED_TODAY'
        else:
            status = 'QUEUED_TOMORROW'
        
        # Формируем данные заказа
        order_data = {
            'idHuman': f"#{datetime.now().strftime('%y%m%d')}{datetime.now().strftime('%H%M%S')[-4:]}",
            'status': status,
            'customer': data.get('customer', {}),
            'items': data.get('items', []),
            'totalAmount': data.get('totalAmount', 0),
            'paymentType': data.get('paymentType', 'CASH'),
            'deliveryDate': delivery_date,
            'timeWindowFrom': data.get('timeWindowFrom', ''),
            'timeWindowTo': data.get('timeWindowTo', ''),
            'regionId': data.get('regionId', ''),
            'operatorId': operator_id,
            'comment': data.get('comment', ''),
            'history': [{
                'by': operator_id,
                'to': status,
                'at': datetime.now().isoformat(),
                'note': 'Заказ создан через Web App',
            }]
        }
        
        # Создаем заказ
        order_id = FirebaseService.create_order(order_data)
        
        return {
            'success': True,
            'order_id': order_id,
            'order': {**order_data, 'id': order_id}
        }
    
    @staticmethod
    async def update_order_status(
        order_id: str,
        new_status: str,
        user_id: str,
        user_role: str,
        reason_code: Optional[str] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Обновить статус заказа"""
        order = FirebaseService.get_order(order_id)
        if not order:
            return {'success': False, 'error': 'Order not found'}
        
        # Проверка прав
        if user_role == 'courier' and order.get('courierId') != user_id:
            if order.get('status') != 'PUBLISHED_TODAY':
                return {'success': False, 'error': 'Permission denied'}
        
        # Обновляем статус
        courier_id = user_id if user_role == 'courier' and new_status == 'ASSIGNED' else None
        
        success = FirebaseService.update_order_status(
            order_id=order_id,
            new_status=new_status,
            user_id=user_id,
            reason_code=reason_code,
            note=note,
            courier_id=courier_id
        )
        
        if success:
            updated_order = FirebaseService.get_order(order_id)
            return {
                'success': True,
                'order': updated_order
            }
        
        return {'success': False, 'error': 'Update failed'}
    
    @staticmethod
    async def get_order_for_display(order_id: str, user_role: str) -> Optional[Dict[str, Any]]:
        """Получить заказ с форматированием для отображения"""
        order = FirebaseService.get_order(order_id)
        if not order:
            return None
        
        # Добавляем форматированные данные
        order['formatted_card'] = format_order_card(order)
        order['keyboard'] = get_order_keyboard(order, user_role)
        
        return order
    
    @staticmethod
    async def get_orders_for_user(user_id: str, user_role: str, filter_type: str = 'all') -> List[Dict[str, Any]]:
        """Получить заказы для пользователя"""
        if filter_type == 'action' and user_role in ['operator', 'admin']:
            return FirebaseService.get_orders_requiring_action(user_id)
        
        if filter_type == 'today':
            today = datetime.now().strftime('%Y-%m-%d')
            if user_role == 'courier':
                return FirebaseService.get_courier_orders(user_id, today)
            return FirebaseService.get_orders_by_date(today)
        
        if filter_type == 'tomorrow':
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            if user_role == 'courier':
                return FirebaseService.get_courier_orders(user_id, tomorrow)
            return FirebaseService.get_orders_by_date(tomorrow)
        
        if user_role == 'courier':
            return FirebaseService.get_courier_orders(user_id)
        
        # Для операторов и логистов - все заказы
        return FirebaseService.get_orders_by_status('NEW')

