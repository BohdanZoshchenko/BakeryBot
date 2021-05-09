# this module is NOT UNIVERSAL for different bots
from modules import *

bot_tree = json_helper.bot_json_to_obj()

bot = telebot.TeleBot(bot_tree["params"]["telegram_token"])

def is_value_valid(msg, level_content):
    type = None
    msg_type = msg.content_type
    value = eval("msg."+msg_type, globals(), locals())
    if "input_type" in level_content.keys():
        type = level_content["input_type"]
        if type == "image":
            type = "photo"
        if type == "text":
            type = "str"
    else:
        return "ok", value
    min = None
    if "min" in level_content.keys():
        min = level_content["min"]
    max = None
    if "max" in level_content.keys():
        max = level_content["max"]
    
    x = None
    type = eval(type)
    x = convert(value, type)
    if not isinstance(x, type) or x==False:
        return "type_mismatch", x
    if isinstance(x, str):
        if min != None and len(x) < min:
            return "too_little", x
        if max != None and len(x) > max:
            return "too_big", x
    else:
        if min != None and x < min:
            return "too_little", x
        if max != None and x > max:
            return "too_big", x
    return "ok", x


def convert(value, type):
    value = str(value)
    if type is float:
        value = value.replace(",", ".")
    try:
        x = type(value)
        return x
    except ValueError:
        return False


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
    bot.send_photo(chat_id, item[2], caption=text, parse_mode="Markdown", reply_markup=markup)

def order_item_start(chat_id, state):
    level = state[0]
    funnel = state[1]
    params = state[2]
    name = params[0]
    text ="*"+name+"*\nЯку вагу бажаєте (від 2 до 102 кілограмів 😊)? Наприклад, 3.25"
    bot.send_message(chat_id, text, parse_mode="Markdown")

def order_item_mass(chat_id, state, sql, param):
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
    text+= str(sum) + " ГРН*"
    text+="\nЧудово. Тепер напишіть побажання щодо смаколика. Наприклад, про начинку і декор або дату бронювання"
    bot.send_message(chat_id, text, parse_mode="Markdown")

def order_item_description(chat_id, state):
    bot.send_message(chat_id, "Супер! Наостанок надішліть фото чи інше зображення, за яким можна зробити декор.")

def order_item_image(chat_id):
    #bot.send_photo(chat_id)
    bot.send_message(chat_id, "ok")

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