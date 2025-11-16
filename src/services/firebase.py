"""Сервис для работы с Firebase Firestore"""
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import os

from src.config import FIREBASE_PROJECT_ID, FIREBASE_CREDENTIALS_PATH

# Инициализация Firebase Admin SDK
if not firebase_admin._apps:
    # Проверяем, есть ли credentials в переменной окружения (для Render)
    firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
    
    if firebase_creds_json:
        # Читаем credentials из переменной окружения
        try:
            print("📝 Загрузка Firebase credentials из переменной окружения...")
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred, {
                'projectId': FIREBASE_PROJECT_ID,
            })
            print("✅ Firebase credentials загружены из переменной окружения")
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга FIREBASE_CREDENTIALS_JSON: {e}")
            print(f"Первые 100 символов: {firebase_creds_json[:100]}")
            raise
        except Exception as e:
            print(f"❌ Ошибка инициализации Firebase: {e}")
            raise
    elif os.path.exists(FIREBASE_CREDENTIALS_PATH):
        # Читаем credentials из файла (для локальной разработки)
        print(f"📝 Загрузка Firebase credentials из файла: {FIREBASE_CREDENTIALS_PATH}")
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {
            'projectId': FIREBASE_PROJECT_ID,
        })
        print("✅ Firebase credentials загружены из файла")
    else:
        # Для разработки можно использовать Application Default Credentials
        print("⚠️ Firebase credentials не найдены.")
        print(f"   Проверьте переменную окружения FIREBASE_CREDENTIALS_JSON или файл {FIREBASE_CREDENTIALS_PATH}")
        print("   Пытаемся использовать Application Default Credentials...")
        try:
            firebase_admin.initialize_app()
            print("✅ Используются Application Default Credentials")
        except Exception as e:
            print(f"❌ Не удалось инициализировать Firebase: {e}")
            raise

db = firestore.client()


class FirebaseService:
    """Сервис для работы с Firestore"""
    
    @staticmethod
    def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя по Telegram ID"""
        users_ref = db.collection('users')
        query = users_ref.where('telegramId', '==', str(telegram_id)).limit(1)
        docs = query.stream()
        
        for doc in docs:
            return {'id': doc.id, **doc.to_dict()}
        return None
    
    @staticmethod
    def create_user(telegram_id: int, display_name: str, role: str, region_id: str) -> str:
        """Создать нового пользователя"""
        user_ref = db.collection('users').document()
        user_ref.set({
            'id': user_ref.id,
            'telegramId': str(telegram_id),
            'displayName': display_name,
            'role': role,
            'regionId': region_id,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP,
        })
        return user_ref.id
    
    @staticmethod
    def get_region(region_id: str) -> Optional[Dict[str, Any]]:
        """Получить регион по ID"""
        doc = db.collection('regions').document(region_id).get()
        if doc.exists:
            return {'id': doc.id, **doc.to_dict()}
        return None
    
    @staticmethod
    def get_all_regions() -> List[Dict[str, Any]]:
        """Получить все регионы"""
        regions = []
        docs = db.collection('regions').stream()
        for doc in docs:
            regions.append({'id': doc.id, **doc.to_dict()})
        return regions
    
    @staticmethod
    def create_order(order_data: Dict[str, Any]) -> str:
        """Создать новый заказ"""
        order_ref = db.collection('orders').document()
        
        # Добавляем timestamp поля
        order_data['createdAt'] = firestore.SERVER_TIMESTAMP
        order_data['updatedAt'] = firestore.SERVER_TIMESTAMP
        
        # Устанавливаем начальный статус
        if 'status' not in order_data:
            delivery_date = order_data.get('deliveryDate', '')
            if delivery_date == datetime.now().strftime('%Y-%m-%d'):
                order_data['status'] = 'PUBLISHED_TODAY'
            else:
                order_data['status'] = 'QUEUED_TOMORROW'
        
        # Инициализируем историю, если её нет
        if 'history' not in order_data:
            order_data['history'] = [{
                'by': order_data.get('operatorId', 'system'),
                'to': order_data['status'],
                'at': datetime.now().isoformat(),
                'note': 'Заказ создан',
            }]
        
        order_ref.set(order_data)
        return order_ref.id
    
    @staticmethod
    def get_order(order_id: str) -> Optional[Dict[str, Any]]:
        """Получить заказ по ID"""
        doc = db.collection('orders').document(order_id).get()
        if doc.exists:
            data = doc.to_dict()
            # Конвертируем Firestore Timestamp в ISO строку
            if 'createdAt' in data and hasattr(data['createdAt'], 'isoformat'):
                data['createdAt'] = data['createdAt'].isoformat()
            if 'updatedAt' in data and hasattr(data['updatedAt'], 'isoformat'):
                data['updatedAt'] = data['updatedAt'].isoformat()
            return {'id': doc.id, **data}
        return None
    
    @staticmethod
    def update_order_status(
        order_id: str,
        new_status: str,
        user_id: str,
        reason_code: Optional[str] = None,
        note: Optional[str] = None,
        courier_id: Optional[str] = None
    ) -> bool:
        """Обновить статус заказа"""
        order_ref = db.collection('orders').document(order_id)
        order_doc = order_ref.get()
        
        if not order_doc.exists:
            return False
        
        current_data = order_doc.to_dict()
        old_status = current_data.get('status', 'NEW')
        
        # Создаем событие истории
        history_event = {
            'by': user_id,
            'from': old_status,
            'to': new_status,
            'at': datetime.now().isoformat(),
            'note': note or f'Статус изменен на {new_status}',
        }
        if reason_code:
            history_event['reasonCode'] = reason_code
        
        # Обновляем заказ
        update_data = {
            'status': new_status,
            'updatedAt': firestore.SERVER_TIMESTAMP,
        }
        
        if courier_id and new_status == 'ASSIGNED':
            update_data['courierId'] = courier_id
        
        if reason_code:
            update_data['reasonCode'] = reason_code
        if note:
            update_data['comment'] = note
        
        # Добавляем событие в историю
        order_ref.update(update_data)
        order_ref.update({
            'history': firestore.ArrayUnion([history_event])
        })
        
        return True
    
    @staticmethod
    def get_orders_by_status(status: str, region_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получить заказы по статусу"""
        orders_ref = db.collection('orders')
        query = orders_ref.where('status', '==', status)
        
        if region_id:
            query = query.where('regionId', '==', region_id)
        
        orders = []
        for doc in query.stream():
            data = doc.to_dict()
            orders.append({'id': doc.id, **data})
        return orders
    
    @staticmethod
    def get_orders_by_date(delivery_date: str, region_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получить заказы по дате доставки"""
        orders_ref = db.collection('orders')
        query = orders_ref.where('deliveryDate', '==', delivery_date)
        
        if region_id:
            query = query.where('regionId', '==', region_id)
        
        orders = []
        for doc in query.stream():
            data = doc.to_dict()
            orders.append({'id': doc.id, **data})
        return orders
    
    @staticmethod
    def get_orders_requiring_action(operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получить заказы, требующие действия оператора"""
        statuses = ['NO_ANSWER', 'BAD_NUMBER', 'FAKE', 'DECLINED', 'RESCHEDULED']
        orders_ref = db.collection('orders')
        
        all_orders = []
        for status in statuses:
            query = orders_ref.where('status', '==', status)
            if operator_id:
                query = query.where('operatorId', '==', operator_id)
            
            for doc in query.stream():
                data = doc.to_dict()
                all_orders.append({'id': doc.id, **data})
        
        return all_orders
    
    @staticmethod
    def get_courier_orders(courier_id: str, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получить заказы курьера"""
        orders_ref = db.collection('orders')
        query = orders_ref.where('courierId', '==', courier_id)
        
        if date:
            query = query.where('deliveryDate', '==', date)
        
        orders = []
        for doc in query.stream():
            data = doc.to_dict()
            orders.append({'id': doc.id, **data})
        return orders
    
    @staticmethod
    def check_duplicate_order(phone: str, delivery_date: str) -> Optional[Dict[str, Any]]:
        """Проверить дубликат заказа по телефону и дате"""
        orders_ref = db.collection('orders')
        query = orders_ref.where('customer.phone', '==', phone).where('deliveryDate', '==', delivery_date)
        
        for doc in query.stream():
            return {'id': doc.id, **doc.to_dict()}
        return None

