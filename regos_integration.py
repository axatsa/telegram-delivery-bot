import os
from typing import Dict, Optional
from datetime import datetime
import logging

from docr.core.api.regos_api import RegosAPI
from docr.schemas.api.docs.cheque import DocChequeGetRequest

logger = logging.getLogger(__name__)



class REGOSIntegration:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        # Используем переданный api_key или извлекаем из base_url
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = base_url.split('/')[-1]
        self.connected_integration_id = self.api_key

    async def create_order(self, order_data: Dict) -> Optional[Dict]:
        """
        Создание нового заказа в системе REGOS
        """
        try:
            async with RegosAPI(self.connected_integration_id) as api:
                # Получаем сервис для работы с чеками
                cheque_service = api.docs.cheque

                # Формируем данные заказа
                items = []
                for item in order_data['items']:
                    items.append({
                        'name': item['name'],
                        'quantity': item['quantity'],
                        'price': item['price'],
                        'total': item['quantity'] * item['price']
                    })

                # Создаем запрос на создание заказа
                # Примечание: Вам нужно уточнить правильный формат запроса в документации REGOS
                # и создать соответствующую модель запроса

                # Пример запроса (замените на актуальный)
                response = await cheque_service.get(
                    DocChequeGetRequest(
                        # Укажите необходимые параметры запроса
                    )
                )

                return response.dict() if response else None

        except Exception as e:
            logger.error(f"Ошибка при создании заказа в REGOS: {e}")
            return None

    async def get_order_status(self, order_id: str) -> Optional[Dict]:
        """
        Получение статуса заказа из REGOS
        """
        try:
            async with RegosAPI(self.connected_integration_id) as api:
                cheque_service = api.docs.cheque
                response = await cheque_service.get_by_uuids([order_id])
                return response[0].dict() if response else None

        except Exception as e:
            logger.error(f"Ошибка при получении статуса заказа: {e}")
            return None

    def update_order_status(self, regos_order_id: str, status: str,
                            comment: str = "") -> bool:
        """
        Обновление статуса заказа в REGOS
        """
        url = f"{self.base_url}orders/{regos_order_id}/status"

        try:
            payload = {
                'status': status,
                'comment': comment,
                'updated_at': datetime.now().isoformat()
            }

            logger.info(f"Обновление статуса заказа: {url}")
            logger.info(f"Данные обновления: {payload}")

            response = requests.put(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при обновлении статуса заказа: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Ответ сервера: {e.response.text}")
            return False

    async def sync_orders(self, db):
        """
        Sync local orders with REGOS system

        Args:
            db: Database instance

        Returns:
            List of sync results
        """
        results = []
        orders_to_sync = db.get_orders_for_regos_sync()

        for order in orders_to_sync:
            # Get user info
            user = db.get_user(order['user_id'])
            if not user:
                logger.error(f"User not found for order {order['id']}")
                continue

            order_data = {
                'user': {
                    'name': user['name'],
                    'phone': user['phone']
                },
                'delivery_address': order['delivery_address'],
                'delivery_date': order['delivery_date'],
                'delivery_time': order['delivery_time'],
                'items': order['items'],
                'total_amount': order['total_amount'],
                'external_id': order['id']
            }

            # Create order in REGOS
            result = await self.create_order(order_data)

            if result and 'id' in result:
                db.set_regos_order_id(order['id'], result['id'])
                results.append({
                    'order_id': order['id'],
                    'regos_order_id': result['id'],
                    'status': 'success',
                    'message': 'Order synced successfully'
                })
            else:
                results.append({
                    'order_id': order['id'],
                    'status': 'error',
                    'message': 'Failed to sync order with REGOS'
                })

        return results
