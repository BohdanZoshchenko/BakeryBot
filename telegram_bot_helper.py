from modules import *

bot_tree = json_helper.bot_json_to_obj()

bot = telebot.TeleBot(bot_tree["params"]["telegram_token"])

global_vars = None
local_vars = None
chat_id = None
sql_result = None

def exec_script(script):
    chat_id = global_vars["chat_id"]
    sql_result = global_vars["sql_result"]
    exec(script, global_vars, local_vars)

def show_items():
    items = sql_result
    markup = types.InlineKeyboardMarkup()
    for item in items:
        button = types.InlineKeyboardButton(item[0]+' '+str(item[3]) +' ГРН/КГ', callback_data='show_item' + item[0])
        markup.add(button)
    bot.send_message(chat_id, "Обирайте 🧐", reply_markup=markup)

def show_single_item():
    print("OOOOOOOOOOOOOOOOOKKKKKKKKKKKKKK")