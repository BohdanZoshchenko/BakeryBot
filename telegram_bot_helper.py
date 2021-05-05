from modules import *

bot_tree = json_helper.bot_json_to_obj()

bot = telebot.TeleBot(bot_tree["params"]["telegram_token"])

def show_items(chat_id, sql_result):
    items = sql_result
    markup = types.InlineKeyboardMarkup()
    for item in items:
        button = types.InlineKeyboardButton(
            '🍰 '+ item[0]+' '+str(item[1]) + ' ГРН/КГ', callback_data='show_item' + item[0])
        markup.add(button)
    bot.send_message(chat_id, "Обирайте 🧐", reply_markup=markup)


def show_single_item(chat_id, param, sql_result):
    item = sql_result[0]
    text = '*'+param+'*\n'
    text += str(item[1])+"\n" #description
    text += str("Ціна: " + str(item[3]) + " ГРН/КГ + за декор окремо") + "\n"#price
    text += "Унікальний декор за вашими побажаннями" + "\n"
    text += "Мінімальна вага до замовлення *2 кг*"
    bot.send_photo(chat_id, item[2], caption=text, parse_mode="Markdown") 
