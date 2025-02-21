import requests
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def send_notification(message: str):
    """
    Отправляет уведомление в Телеграм.
    """
    log.debug(f"Отправляю сообщение в ТГ бота: {message}")
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    requests.post(url, data=data)