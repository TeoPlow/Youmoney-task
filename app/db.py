import sqlite3
import logging
from config import DATABASE_NAME

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def init_db() -> None:
    log.debug('Инициализация БД')
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='payments_status';
            """
        )
        exists = cursor.fetchone()
        if not exists:
            log.debug('Создание таблицы payments_status')
            cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS 'payments_status' (
                    payment_id VARCHAR(40) PRIMARY KEY,
                    order_id INT NOT NULL,
                    user_id TEXT NOT NULL,
                    status VARCHAR(16) NOT NULL
                );
                """
            )
            conn.commit()
        log.debug('БД инициализирована')


def get_payments_id(status: str) -> list[str]:
    log.debug(f'Получение из БД списка платежей со статусом {status}')
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT payment_id FROM 'payments_status'
            WHERE status = ?;
            """, (status, )
        )
        return cursor.fetchall()


def update_payment_status(payment_id: str, status: str) -> None:
    log.debug(f'Обновление статуса платежа {payment_id} на {status} в БД')
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE payments_status
            SET status = ?
            WHERE payment_id = ?;
            """, (status, payment_id)
        )
        conn.commit()


def add_payment(payment_id: str,
                order_id: int,
                user_id: str,
                status: str) -> None:
    log.debug(f'Добавление платежа {payment_id} в БД')
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO payments_status (payment_id, order_id, user_id, status)
            VALUES (?, ?, ?, ?);
            """, (payment_id, order_id, user_id, status)
        )
        conn.commit()
