import uuid
import logging
from typing import Dict, Tuple
from yookassa import Configuration, Payment, Refund
from yookassa.domain.response import PaymentResponse, RefundResponse
from yookassa.domain.exceptions.bad_request_error import BadRequestError
from config import YKASSA_SECRET_KEY, YKASSA_SHOP_ID, RETURN_URL
from celery import group
from celery_tasks import check_payment_task, check_refund_task
from db import get_payment

Configuration.account_id = YKASSA_SHOP_ID
Configuration.secret_key = YKASSA_SECRET_KEY

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def create_payment(data: Dict) -> Tuple[str, str]:
    payment_id = str(uuid.uuid4())
    payment = Payment.create({
        "amount": data['amount'],
        "confirmation": {
            "type": "redirect",
            "return_url": f'{RETURN_URL}/{payment_id}'
        },
        "capture": True,
        "description": f"Заказ №{data['order_id']}"
    }, payment_id)

    payment_data = check_payment_task.apply_async((payment.id, ),
                                                  countdown=1)
    log.info(f'Платёж {payment.id} создан: \nИНФО: {payment_data}')
    return (payment.confirmation.confirmation_url, payment.id)


def check_payment(payment_id: str) -> PaymentResponse:
    payment_data = check_payment_task.apply_async((payment_id, True),
                                                  countdown=1)
    response = payment_data.get(timeout=None)
    return response

# БД выкрутил
"""
def recheck_payments_status() -> None:
    log.debug('Перепроверяю статусы платежей, '
              'если будут pending - перезапишу их в БД')
    pending_payments_id = get_payments_id('pending')

    log.debug(f"Получил список платежей: {pending_payments_id}")

    task_group = group(
        recheck_payments_task.s(payment_id)
        for payment_id in pending_payments_id
    )

    result = task_group.apply_async()
    log.debug(f'Группа задач создана: {result.id}')

    while not result.ready():
        log.debug('Жду, пока задачи закончат свое выполнение')
        pass

    log.debug('Группа задач выполнена')
"""

def refund_payment(data: Dict):
    if not get_payment(data['payment_id']):
        raise BadRequestError
    refund = Refund.create({
        "amount": {
            "value": f"{data['amount']['value']}",
            "currency": f"{data['amount']['currency']}"
        },
        "payment_id": f'{data['payment_id']}'
    })

    refund_data = check_refund_task.apply_async((refund.id, ),
                                                  countdown=1)
    log.info(f'Возврат с ID: {refund.id} создан: \nИНФО: {refund_data}')
    return refund.json()
