import logging
import time
from celery import Celery
from yookassa import Payment, Configuration, Refund
from notification import send_notification
from datetime import timedelta, datetime
from config import (
    YKASSA_SHOP_ID,
    YKASSA_SECRET_KEY,
    RETURN_URL,
    CHECK_PAYMENT_STATUS_PERIOD,
    REDIS_URL
)


Configuration.account_id = YKASSA_SHOP_ID
Configuration.secret_key = YKASSA_SECRET_KEY

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

celery = Celery('tasks',
                broker=REDIS_URL,
                backend=REDIS_URL)


@celery.task
def retry_payment_task(id: str, amount: dict, description: int):
    log.info('TASK: Повторение платежа')
    payment = Payment.create({
        "amount": amount,
        "confirmation": {
            "type": "redirect",
            "return_url": f'{RETURN_URL}'
        },
        "capture": True,
        "description": f"Прошлый платёж не прошёл, повторяю: {description}"
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
        pay_data = Payment.find_one(id)
        if pay_data.status == "pending":
            log.info(f'Платёж {pay_data.id} ожидает обработки')
            if one_check:
                break
            pass
        elif pay_data.status == "succeeded":
            message = f'Платёж {pay_data.id} принят - {pay_data.description}'
            log.info(message)
            send_notification(message)
            break
        elif pay_data.status == "canceled":
            message = f"""Платёж {pay_data.id} отменён - {pay_data.description}
            Причина: {pay_data.cancellation_details.reason}"""
            log.info(message)
            send_notification(message)
            if not one_check:
                log.info(f'Платёж {pay_data.id} повторится через сутки')
                next_time = datetime.now() + timedelta(minutes=2)
                # next_time = datetime.now() + timedelta(days=1)
                retry_payment_task.apply_async(
                    id, pay_data.amount, pay_data.description, eta=next_time
                )
            break
        else:
            error_msg = f'Неизвестный status: {pay_data.status}'
            log.error(error_msg)
            raise Exception(error_msg)

    # update_payment_status(pay_data.id, pay_data.status)
    return pay_data.json()


@celery.task
def check_refund_task(id: str) -> str:
    log.info('TASK: Проверяет статус возврата')
    while True:
        time.sleep(CHECK_PAYMENT_STATUS_PERIOD)
        refund_data = Refund.find_one(id)
        description = refund_data.description or "Без описания"

        if refund_data.status == "pending":
            log.info(f'Возврат {refund_data.id} ожидает обработки.')
            pass
        elif refund_data.status == "succeeded":
            message = f'Возврат {refund_data.id} принят - {description}'
            log.info(message)
            send_notification(message)
            break
        elif refund_data.status == "canceled":
            message = f"""Возврат {refund_data.id} отменён - {description}
            Причина: {refund_data.cancellation_details.reason}"""
            log.info(message)
            send_notification(message)
            break
        else:
            error_msg = f'Неизвестный status: {refund_data.status}'
            log.error(error_msg)
            raise Exception(error_msg)

    return refund_data.json()
