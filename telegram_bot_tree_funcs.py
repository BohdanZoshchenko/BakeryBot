# this module is NOT UNIVERSAL for different bots
from modules import *
from settings import *

async def show_items(chat_id, sql_result):
    print("items")
    items = sql_result
    markup = types.InlineKeyboardMarkup()
    for item in items:
        button = types.InlineKeyboardButton(
            '🍰 '+ item[0]+' '+str(item[1]) + ' ГРН/КГ', callback_data='show_item%' + item[0])
        markup.add(button)
    await bot.send_message(chat_id, "Обирайте 🧐", reply_markup=markup)


async def show_single_item(chat_id, param, sql_result):
    item = sql_result[0]
    text = '*'+param[0]+'*\n'
    text += str(item[1])+"\n" #description
    text += str("Ціна: " + str(item[3]) + " ГРН/КГ + за декор окремо") + "\n"#price
    text += "Унікальний декор за вашими побажаннями" + "\n"
    text += "Мінімальна вага до замовлення 2 кг"
    markup = types.InlineKeyboardMarkup()
    order_button = types.InlineKeyboardButton(
            'Замовити', callback_data='order_item%' + param[0])
    markup.add(order_button)
    info_button = types.InlineKeyboardButton(
            'Інфо', callback_data='info_in_telegram')
    back_button = types.InlineKeyboardButton(
            'Назад', callback_data='new_greeting')
    markup.row(info_button, back_button)
    await bot.send_photo(chat_id, item[2], caption=text, parse_mode="Markdown", reply_markup=markup)

async def order_item_start(chat_id, state):
    level = state[0]
    funnel = state[1]
    params = state[2]
    name = params[0]
    text ="*"+name+"*\nЯку вагу бажаєте (від 2 до 102 кілограмів 😊)? Наприклад, 3.25"
    await bot.send_message(chat_id, text, parse_mode="Markdown")

async def order_item_mass(chat_id, state, sql, param):
    level = state[0]
    funnel = state[1]
    params = state[2]
    name = params[0]
    mass = param

    price = db_helper.do_sql(sql, [name])[0][0]
    sum = float(price)*float(mass)
    sum = price_format(sum)

    text = "*"+ name+"\n"
    text+= str(mass) + " кг x " + str(price) + " = "
    text+= str(sum) + " ГРН + за декор окремо*"
    text+="\nЧудово! Ви підтверджуєте замовлення?"

    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(types.InlineKeyboardButton('Підтверджую', callback_data="accept_order"+text))
    inline_kb.add(types.InlineKeyboardButton('Подумаю ще', callback_data='new_greeting'))

    await bot.send_message(chat_id, text, parse_mode="Markdown")

async def handle_order():
    pass

def price_format(price):
    price = float(price)
    price = round(price, 2)
    if not "." in str(price):
        return price
    price = str(price).split('.')
    while len(price[1]) < 2:
        price[1] += "0"
    price = price[0] + "." + price[1]
    return price