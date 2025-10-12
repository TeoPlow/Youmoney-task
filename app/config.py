import dotenv
import os

dotenv.load_dotenv()

API_HOST = os.getenv('API_HOST')
API_PORT = int(os.getenv('API_PORT'))

YKASSA_SECRET_KEY = os.getenv('YKASSA_SECRET_KEY')
YKASSA_SHOP_ID = os.getenv('YKASSA_SHOP_ID')
RETURN_URL = os.getenv('RETURN_URL')
CHECK_PAYMENT_STATUS_PERIOD = int(os.getenv('CHECK_PAYMENT_STATUS_PERIOD'))
DATABASE_NAME = os.getenv('DATABASE_NAME')

current_dir = os.getcwd()
DATABASE_PATH = os.path.join(current_dir, DATABASE_NAME)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
