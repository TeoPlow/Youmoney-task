import logging
import time
from celery import Celery
from yookassa import Payment, Configuration
from yookassa.domain.response import PaymentResponse
from datetime import timedelta, datetime
from db import update_payment_status
from config import (CHECK_PAYMENT_STATUS_PERIOD,
                    YKASSA_SECRET_KEY,
                    YKASSA_SHOP_ID)

Configuration.account_id = YKASSA_SHOP_ID
Configuration.secret_key = YKASSA_SECRET_KEY

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

celery = Celery('tasks',
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0')


@celery.task
def retry_payment_task(id: str):
    log.info('TASK: Повторение платежа спустя сутки')
    pass
    # Суды код для повторной обработки платежа


@celery.task
def check_payment_task(id: str, one_check=False) -> PaymentResponse:
    log.info('TASK: Проверяет статус платежа')
    while True:
        time.sleep(CHECK_PAYMENT_STATUS_PERIOD)
        payment_data = Payment.find_one(id)
        if payment_data.status == "pending":
            log.info(f'Платёж {payment_data.id} ожидаёт обработки')
            if one_check:
                break
            pass
        elif payment_data.status == "succeeded":
            log.info(f'Платёж {payment_data.id} принят')
            break
        elif payment_data.status == "canceled":
            log.info(f'Платёж {payment_data.id} отменён')
            if not one_check:
                log.info(f'Платёж {payment_data.id} повторится через сутки')
                next_time = datetime.now() + timedelta(days=1)
                retry_payment_task.apply_async(id, eta=next_time)
            break
        else:
            error_msg = f'Неизвестный status: {payment_data.status}'
            log.error(error_msg)
            raise Exception(error_msg)

    update_payment_status(payment_data.id, payment_data.status)
    return payment_data.json()


@celery.task
def recheck_payments_task(id: str) -> None:
    log.info('TASK: Повторная проверка статуса платежей'
             ' и обновление информации о них в БД')
    try:
        payment_data: PaymentResponse = Payment.find_one(id)
        update_payment_status(payment_data.id, payment_data.status)
    except ValueError as e:
        log.error(f'Беда, payment_id неверный, перепроверка неуспешна: {e}')
