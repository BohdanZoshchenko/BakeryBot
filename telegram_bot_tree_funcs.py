# this module is NOT UNIVERSAL for different bots
from modules import *

bot_tree = json_helper.bot_json_to_obj()

bot = telebot.TeleBot(bot_tree["params"]["telegram_token"])

def show_items(chat_id, sql_result):
    items = sql_result
    markup = types.InlineKeyboardMarkup()
    for item in items:
        button = types.InlineKeyboardButton(
            '🍰 '+ item[0]+' '+str(item[1]) + ' ГРН/КГ', callback_data='show_item%' + item[0])
        markup.add(button)
    bot.send_message(chat_id, "Обирайте 🧐", reply_markup=markup)


def show_single_item(chat_id, param, sql_result):
    item = sql_result[0]
    text = '*'+param+'*\n'
    text += str(item[1])+"\n" #description
    text += str("Ціна: " + str(item[3]) + " ГРН/КГ + за декор окремо") + "\n"#price
    text += "Унікальний декор за вашими побажаннями" + "\n"
    text += "Мінімальна вага до замовлення 2 кг"
    markup = types.InlineKeyboardMarkup()
    order_button = types.InlineKeyboardButton(
            'Замовити', callback_data='order_item%' + param)
    markup.add(order_button)
    info_button = types.InlineKeyboardButton(
            'Інфо', callback_data='info_in_telegram')
    back_button = types.InlineKeyboardButton(
            'Назад', callback_data='new_greeting')
    markup.row(info_button, back_button)
    bot.send_photo(chat_id, item[2], caption=text, parse_mode="Markdown", reply_markup=markup)

def order_item1(chat_id, state):
    level = state[0]
    funnel = state[1]
    params = state[2]
    name = params[0]
    text ="*"+name+"*\nЧудово! Яку вагу бажаєте (від 2 до 102 кілограмів 😊)? Наприклад, 3.25"
    bot.send_text(chat_id, text, parse_mode="Markdown")

def order_funnel_on_type_kg(input, param):
    out = "\n" + str(input) + " кг * " + str(param) + " = " + str(round(input*param, 2)) + " ГРН"
    print(out)