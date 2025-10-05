import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_name="shop_bot_regos2.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                registered_at TEXT NOT NULL
            )
        ''')

        # Таблица категорий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                emoji TEXT
            )
        ''')

        # Таблица товаров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                unit TEXT NOT NULL,
                category_id INTEGER,
                image BLOB,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')

        # Таблица корзин
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS carts (
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')

        # Таблица заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_amount REAL NOT NULL,
                delivery_date TEXT NOT NULL,
                delivery_time TEXT NOT NULL,
                delivery_address TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                regos_order_id TEXT,
                regos_status TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Таблица элементов заказа
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')

        # Добавляем стандартные категории если их нет
        default_categories = [
            ("Фрукты", "🍎"),
            ("Овощи", "🥕"),
            ("Ягоды", "🍓"),
            ("Молочка", "🥛")
        ]

        cursor.executemany('''
            INSERT OR IGNORE INTO categories (name, emoji) VALUES (?, ?)
        ''', default_categories)

        conn.commit()
        conn.close()
        logger.info("База данных инициализирована")

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    # === USER METHODS ===
    def get_user(self, user_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, name, phone FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        if user:
            return {"user_id": user[0], "name": user[1], "phone": user[2]}
        return None

    def add_user(self, user_id: int, name: str, phone: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, name, phone, registered_at) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, phone, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    # === CATEGORY METHODS ===
    def get_categories(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, emoji FROM categories')
        categories = cursor.fetchall()
        conn.close()
        return [{"id": cat[0], "name": f"{cat[1]} {cat[2]}", "raw_name": cat[1]} for cat in categories]

    # === PRODUCT METHODS ===
    def get_products_by_category(self, category_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, price, quantity, unit, image 
            FROM products WHERE category_id = ?
        ''', (category_id,))
        products = cursor.fetchall()
        conn.close()
        return [{"id": p[0], "name": p[1], "price": p[2], "quantity": p[3], "unit": p[4], "image": p[5]} for p in
                products]

    def get_product(self, product_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, price, quantity, unit, image FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        conn.close()
        if product:
            return {"id": product[0], "name": product[1], "price": product[2], "quantity": product[3],
                    "unit": product[4], "image": product[5]}
        return None

    def add_product(self, name: str, price: float, quantity: int, category_id: int, image_data: bytes = None) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (name, price, quantity, unit, category_id, image)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, price, quantity, "кг", category_id, image_data))
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return product_id

    def delete_product(self, product_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def get_all_products(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.id, p.name, p.price, p.quantity, p.unit, c.name 
            FROM products p 
            JOIN categories c ON p.category_id = c.id
        ''')
        products = cursor.fetchall()
        conn.close()
        return [{"id": p[0], "name": p[1], "price": p[2], "quantity": p[3], "unit": p[4], "category": p[5]} for p in
                products]

    # === CART METHODS ===
    def get_user_cart(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.id, p.name, p.price, p.unit, c.quantity 
            FROM carts c 
            JOIN products p ON c.product_id = p.id 
            WHERE c.user_id = ?
        ''', (user_id,))
        cart_items = cursor.fetchall()
        conn.close()
        return [{"id": item[0], "name": item[1], "price": item[2], "unit": item[3], "quantity": item[4]} for item in
                cart_items]

    def add_to_cart(self, user_id: int, product_id: int, quantity: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO carts (user_id, product_id, quantity) 
            VALUES (?, ?, ?)
        ''', (user_id, product_id, quantity))
        conn.commit()
        conn.close()

    def clear_cart(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM carts WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    # === ORDER METHODS ===
    def update_order_status(self, order_id: int, status: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders SET status = ? WHERE id = ?
        ''', (status, order_id))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    def set_regos_order_id(self, order_id: int, regos_order_id: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders 
            SET regos_order_id = ?, regos_status = 'pending' 
            WHERE id = ?
        ''', (regos_order_id, order_id))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    def create_order(self, user_id: int, total_amount: float, delivery_date: str,
                     delivery_time: str, delivery_address: str, cart_items: List[Dict]):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create the order
        cursor.execute('''
            INSERT INTO orders (
                user_id, total_amount, delivery_date, 
                delivery_time, delivery_address, created_at,
                status, regos_order_id, regos_status
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending', NULL, 'not_synced')
        ''', (user_id, total_amount, delivery_date, delivery_time,
              delivery_address, datetime.now().isoformat()))

        order_id = cursor.lastrowid

        # Add order items
        for item in cart_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item.get('id', item.get('product_id')), item['quantity'], item['price']))

        # Clear the user's cart
        cursor.execute('DELETE FROM carts WHERE user_id = ?', (user_id,))

        conn.commit()
        conn.close()
        return order_id

    def update_regos_status(self, order_id: int, regos_status: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders 
            SET regos_status = ? 
            WHERE id = ?
        ''', (regos_status, order_id))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    def get_orders_for_regos_sync(self):
        """Get all orders that need to be synced with REGOS"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, user_id, total_amount, delivery_date, delivery_time, 
                   delivery_address, created_at
            FROM orders 
            WHERE regos_status = 'not_synced' OR regos_status IS NULL
        ''')
        orders = cursor.fetchall()
        
        result = []
        for order in orders:
            # Get order items
            cursor.execute('''
                SELECT p.name, oi.quantity, oi.price
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            ''', (order[0],))
            items = cursor.fetchall()
            
            result.append({
                'id': order[0],
                'user_id': order[1],
                'total_amount': order[2],
                'delivery_date': order[3],
                'delivery_time': order[4],
                'delivery_address': order[5],
                'created_at': order[6],
                'items': [{'name': i[0], 'quantity': i[1], 'price': i[2]} for i in items]
            })
            
        conn.close()
        return result

    def get_order_by_id(self, order_id: int):
        """Get order by ID with all details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get order info
        cursor.execute('''
            SELECT id, user_id, total_amount, delivery_date, delivery_time, 
                   delivery_address, status, regos_order_id, regos_status, created_at
            FROM orders 
            WHERE id = ?
        ''', (order_id,))
        
        order_data = cursor.fetchone()
        if not order_data:
            return None
            
        # Get order items
        cursor.execute('''
            SELECT p.name, oi.quantity, oi.price, p.unit
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order_id,))
        items = cursor.fetchall()
        
        # Get user info
        cursor.execute('''
            SELECT name, phone FROM users WHERE user_id = ?
        ''', (order_data[1],))
        user_data = cursor.fetchone()
        
        conn.close()
        
        return {
            'id': order_data[0],
            'user': {
                'id': order_data[1],
                'name': user_data[0] if user_data else 'Unknown',
                'phone': user_data[1] if user_data else 'Unknown'
            },
            'total_amount': order_data[2],
            'delivery_date': order_data[3],
            'delivery_time': order_data[4],
            'delivery_address': order_data[5],
            'status': order_data[6],
            'regos_order_id': order_data[7],
            'regos_status': order_data[8] or 'not_synced',
            'created_at': order_data[9],
            'items': [{
                'name': i[0],
                'quantity': i[1],
                'price': i[2],
                'unit': i[3]
            } for i in items]
        }