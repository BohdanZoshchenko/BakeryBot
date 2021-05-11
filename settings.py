
from modules import *

bot_tree = json_helper.bot_json_to_obj()

bot = Bot(bot_tree["params"]["telegram_token"])

dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

BOT_TOKEN = bot_tree["params"]["telegram_token"]
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

# webhook settings
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'