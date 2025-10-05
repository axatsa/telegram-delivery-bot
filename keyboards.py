from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import Database

db = Database()


def get_main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Каталог"), KeyboardButton(text="🛍️ Корзина")]
        ],
        resize_keyboard=True
    )


def get_phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_categories_keyboard():
    categories = db.get_categories()
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(text=category["name"], callback_data=f"category_{category['id']}")])
    keyboard.append([InlineKeyboardButton(text="🛍️ Перейти в корзину", callback_data="view_cart")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_products_keyboard(category_id: int):
    products = db.get_products_by_category(category_id)
    keyboard = []
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product['name']} - {product['price']}сум/{product['unit']}",
                callback_data=f"product_{product['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_quantity_keyboard(current_quantity: int = 0):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➖", callback_data="qty_minus"),
                InlineKeyboardButton(text=f"{current_quantity} кг", callback_data="qty_current"),
                InlineKeyboardButton(text="➕", callback_data="qty_plus")
            ],
            [
                InlineKeyboardButton(text="✅ Добавить в корзину", callback_data="add_to_cart"),
                InlineKeyboardButton(text="🛒 Продолжить покупки", callback_data="continue_shopping")
            ]
        ]
    )


def get_cart_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 В каталог"), KeyboardButton(text="💳 К оформлению")]
        ],
        resize_keyboard=True
    )


def get_cart_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛒 Продолжить покупки", callback_data="continue_shopping"),
                InlineKeyboardButton(text="💳 Оформить заказ", callback_data="start_checkout_inline")
            ],
            [InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")]
        ]
    )


def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить товар"), KeyboardButton(text="✏️ Изменить товар")],
            [KeyboardButton(text="🗑 Удалить товар"), KeyboardButton(text="📋 Список товаров")],
            [KeyboardButton(text="📦 Управление заказами REGOS")],
            [KeyboardButton(text="🔙 Выйти из админки")]
        ],
        resize_keyboard=True
    )

def get_categories_admin_keyboard():
    categories = db.get_categories()
    keyboard = [[KeyboardButton(text=cat["name"])] for cat in categories]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )


# keyboards.py - обновите функцию get_edit_product_keyboard()

def get_edit_product_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Название"), KeyboardButton(text="Цена")],
            [KeyboardButton(text="Количество"), KeyboardButton(text="Категория")],
            [KeyboardButton(text="Фото"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )


def get_skip_photo_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="пропустить")]],
        resize_keyboard=True
    )


def get_location_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_confirm_order_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")
            ]
        ]
    )


def get_regos_orders_keyboard():
    """Get keyboard for REGOS orders management"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Синхронизировать заказы", callback_data="sync_regos_orders"),
                InlineKeyboardButton(text="ℹ️ Проверить статус", callback_data="check_regos_status")
            ],
            [
                InlineKeyboardButton(text="✏️ Обновить статус", callback_data="update_regos_status"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")
            ]
        ]
    )

def get_regos_status_keyboard():
    """Get keyboard with common REGOS status options"""
    keyboard = [
        [KeyboardButton(text="pending"), KeyboardButton(text="processing")],
        [KeyboardButton(text="shipped"), KeyboardButton(text="delivered")],
        [KeyboardButton(text="cancelled"), KeyboardButton(text="on_hold")],
        [KeyboardButton(text="🔙 Назад к заказам")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
