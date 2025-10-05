from decimal import Decimal
from typing import List

from schemas.api.docs.cash_amount_details import CashAmountDetails
from schemas.api.docs.cash_session import DocCashSession
from schemas.api.docs.retail_payment import DocRetailPayment
from schemas.api.reports.retail_report.count import Counts
from schemas.api.reports.retail_report.payment import Payment
from ..utils import format_money, format_timestamp
from schemas.api.docs.cheque import DocCheque
from schemas.api.docs.cheque_operation import DocChequeOperation


def format_cheque_notification(*, cheque: DocCheque, action: str) -> str:
    """
    Creates a formatted notification message for a cheque.
    Expects a cheque object with attributes: code, amount, is_return, date.
    The action parameter is either "DocChequeClosed" or "DocChequeCanceled".
    """
    # Determine status text based on action
    status_text = "✅ ЧЕК ЗАКРЫТ" if action.lower() == "DocChequeClosed".lower() else "🚫 ЧЕК ОТМЕНЕН"
    
    # Build the main message
    message_parts = [
        f"*{status_text}*",
        "----------------------",
        f"* {'Возврат' if cheque.is_return else 'Продажа'} *",
        "----------------------",
        f"*Код:* `{cheque.code}`",
        f"*Дата:* `{format_timestamp(cheque.date)}`",
        f"*Сумма:* `{format_money(cheque.amount) }`",
        "----------------------"
    ]
    
    return "\n".join(message_parts)


def format_session_notification(*, session: DocCashSession, action: str) -> str:
    """
    Creates a formatted notification message for a session.
    Expects a session object with attributes: code, operating_cash_id, start_date, close_date, closed, close_amount.
    The action parameter is either "DocSessionOpened" or "DocSessionClosed".
    """
    # Determine session state text
    state_text = "ОТКРЫТА" if action.lower() == "DocSessionOpened".lower() else "ЗАКРЫТА"
    
    # Build the message
    message = [
        f"*СМЕНА {state_text}*",
        f"*{session.code}*",
        "----------------------",
        f"*Касса:* {session.operating_cash_id}",
        "----------------------",
        f"*Открыл(а):*",
        f"{format_timestamp(session.start_date)}",
        f"_{session.start_user.full_name}_\n"
    ]

    if session.closed:
        message.extend([
            "----------------------",
            f"*Закрыл(а):*",
            f"{format_timestamp(session.close_date)}",
            f"_{session.close_user.full_name}_\n"
        ])

    return "\n".join(message)


def format_cheque_details(*, cheque: DocCheque, operations: List[DocChequeOperation], payments: List[DocRetailPayment]) -> str:
    """
    Creates a formatted message for cheque details, including itemized operations.
    """
    
    # Build the header
    message_parts = [
        "*ДЕТАЛИ ЧЕКА*",
        "----------------------",
        f"* {'Возврат' if cheque.is_return else 'Продажа'} *",
        "----------------------",
        f"*Код:* `{cheque.code}`",
        f"*Дата:* `{format_timestamp(cheque.date)}`",
        "----------------------",
    ]
    
    # Process operations (items)
    if not operations:
        message_parts.append("_Нет товаров._")
    else:
        max_items = 30  # Limit the number of items displayed
        for index, operation in enumerate(operations, start=1):
            item = getattr(operation, "item", None)
            name = (
                getattr(item, "name", None)
                or getattr(item, "fullname", None)
                or "No name"
            )
            quantity = getattr(operation, "quantity", None)
            price = getattr(operation, "price", None)
            
            # Calculate total for the item
            try:
                item_total = quantity * price if quantity is not None and price is not None else None
            except Exception:
                item_total = None
            
            # Format values
            quantity_text = f"{quantity}" if quantity is not None else "0"
            price_text = format_money(price) if price is not None else "0.00 "
            total_text = format_money(item_total) if item_total is not None else "0.00 "
            
            # Add item line
            message_parts.append(f"{index}. *{name}*\n `{quantity_text} × {price_text} = {total_text}`")
            
            # Truncate if exceeding max items
            if index >= max_items:
                message_parts.append("_…Список товаров ограничен 30 позициями_")
                break
    message_parts.append("----------------------")
    message_parts.append(f"*Итого:* `{format_money(cheque.amount)}`")
    message_parts.append("----------------------")
    if not payments:
        message_parts.append("_Нет оплат._")
    else:
        for payment in payments:
            payment_type = payment.type.name
            value = getattr(payment, "value", 0)
            message_parts.append(f"{payment_type}: `{format_money(value)}`")
    message_parts.append("━━━━━━━━━━━━━━")
    return "\n".join(message_parts)


def format_session_details(*, session: DocCashSession,operations: CashAmountDetails, counts: Counts, payments: List[Payment]) -> str:

    def _dec(x) -> Decimal:
        if isinstance(x, Decimal):
            return x
        if x is None:
            return Decimal("0")
        return Decimal(str(x))

    # Итоги по продажам и возвратам
    total_sales: Decimal = sum((_dec(p.sale_amount) for p in payments), Decimal("0"))
    total_returns: Decimal = sum((_dec(p.return_amount) for p in payments), Decimal("0"))
    
    count = counts[0] if counts else Counts()

    message = [
        f"*ДЕТАЛИ СМЕНЫ*",
        f"*{session.code}*",
        "----------------------",
        f"*Касса:* {session.operating_cash_id}",
        "----------------------",
        f"*Открыл(а):*",
        f"{format_timestamp(session.start_date)}",
        f"_{session.start_user.full_name}_\n"
        "----------------------",
        f"*Закрыл(а):*",
        f"{format_timestamp(session.close_date)}",
        f"_{session.close_user.full_name}_\n"
        "----------------------",
        "*ИТОГИ ПРОДАЖ*",
        "----------------------",
        f"*Кол-во чеков продаж:* `{(count.sale_count)}`",
        f"*Сумма продаж:* `{format_money(total_sales)}`",

        f"*Кол-во чеков возвратов:* `{(count.return_count)}`",
        f"*Сумма возвратов:* `{format_money(total_returns)}`",

        f"*Поступление:* `{format_money(total_sales - total_returns)}`",
        f"*Выручка:* `{format_money(total_sales - total_returns - _dec(count.debt_paid_amount)) }`",
        f"*Выдано в долг:* `{format_money(count.debt_amount)}`",
        f"*Оплачено долга:* `{format_money(count.debt_paid_amount)}`",
        "****************************",
        f"*Валовая прибыль:* `{format_money(count.gross_profit)}`",

    ]

    if  payments: 
        message.extend([
        "----------------------",
        "*ПЛАТЕЖИ*",
        "----------------------"
        ])
        for payment in payments:
            message.append(f"*{payment.payment_type_name}*:")
            message.append(f"_ - Продажи_: `{format_money(payment.sale_amount)}`")
            message.append(f"_ - Возвраты_: `{format_money(payment.return_amount)}`")
    
    message.extend([   
        "\n----------------------\n"
        "*КОНТРОЛЬ НАЛИЧНОЙ КАССЫ*",
        "----------------------",
        f"*На открытие:* `{format_money(operations.start_amount)}`",
        f"*Внесения:* `{format_money(operations.income)}`",
        f"*Изъятия:* `{format_money(operations.outcome)}`",
        f"*На закрытие:* `{format_money(operations.end_amount)}`",
    ])


    

    return "\n".join(message)
