import logging
import time
from celery import Celery
from yookassa import Payment, Configuration, Refund
from yookassa.domain.response import PaymentResponse
from notification import send_notification
from datetime import timedelta, datetime
from db import get_payment
from config import (CHECK_PAYMENT_STATUS_PERIOD,
                    YKASSA_SECRET_KEY,
                    YKASSA_SHOP_ID,
                    RETURN_URL)

Configuration.account_id = YKASSA_SHOP_ID
Configuration.secret_key = YKASSA_SECRET_KEY

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

celery = Celery('tasks',
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0')


@celery.task
def retry_payment_task(id: str, amount: dict, description: int):
    log.info('TASK: Повторение платежа')
    payment = Payment.create({
        "amount": amount,
        "confirmation": {
            "type": "redirect",
            "return_url": f'{RETURN_URL}/{id}'
        },
        "capture": True,
        "description": f"Прошлый платёж не прошёл. Повторная оплата. {description}"
    }, id)
    
    message = f"""
    Повторный платёж {payment.id} создан.
    Ссылка на платёж:
    {payment.confirmation.confirmation_url}
    """
    log.info(message)
    send_notification(message)


@celery.task
def check_payment_task(id: str, one_check=False) -> str:
    log.info('TASK: Проверяет статус платежа')
    while True:
        time.sleep(CHECK_PAYMENT_STATUS_PERIOD)
        payment_data = Payment.find_one(id)
        if payment_data.status == "pending":
            log.info(f'Платёж {payment_data.id} ожидаёт обработки.')
            if one_check:
                break
            pass
        elif payment_data.status == "succeeded":
            message = f'Платёж {payment_data.id} принят. Описание: {payment_data.description}'
            log.info(message)
            send_notification(message)
            break
        elif payment_data.status == "canceled":
            message = f"""Платёж {payment_data.id} отменён. Описание: {payment_data.description}
            Причина: {payment_data.cancellation_details.reason}"""
            log.info(message)
            send_notification(message)
            if not one_check:
                log.info(f'Платёж {payment_data.id} повторится через сутки')
                next_time = datetime.now() + timedelta(minutes=2)
                # next_time = datetime.now() + timedelta(days=1)
                retry_payment_task.apply_async(id, payment_data.amount, payment_data.description, eta=next_time)
            break
        else:
            error_msg = f'Неизвестный status: {payment_data.status}'
            log.error(error_msg)
            raise Exception(error_msg)

    # update_payment_status(payment_data.id, payment_data.status)
    return payment_data.json()

# БД выкрутил
"""
@celery.task
def recheck_payments_task(id: str) -> None:
    log.info('TASK: Повторная проверка статуса платежей'
             ' и обновление информации о них в БД')
    try:
        payment_data: PaymentResponse = Payment.find_one(id)
        update_payment_status(payment_data.id, payment_data.status)
    except ValueError as e:
        log.error(f'Беда, payment_id неверный, перепроверка неуспешна: {e}')
"""


@celery.task
def check_refund_task(id: str) -> str:
    log.info('TASK: Проверяет статус возврата')
    while True:
        time.sleep(CHECK_PAYMENT_STATUS_PERIOD)
        refund_data = Refund.find_one(id)
        if refund_data.status == "pending":
            log.info(f'Возврат {refund_data.id} ожидаёт обработки.')
            pass
        elif refund_data.status == "succeeded":
            message = f'Возврат {refund_data.id} принят. Описание: {refund_data.description}'
            log.info(message)
            send_notification(message)
            break
        elif refund_data.status == "canceled":
            message = f"""Возврат {refund_data.id} отменён. Описание: {refund_data.description}
            Причина: {refund_data.cancellation_details.reason}"""
            log.info(message)
            send_notification(message)
            break
        else:
            error_msg = f'Неизвестный status: {refund_data.status}'
            log.error(error_msg)
            raise Exception(error_msg)

    return refund_data.json()
