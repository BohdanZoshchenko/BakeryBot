# this module is NOT UNIVERSAL for different bots
from modules import *
from settings import *

def set_user_state(chat_id, state):
    if state == None:
        state = [None, None, None]
    level = str(state[0])
    funnel = str(state[1])
    params = state[2]
    db_helper.do_sql(bot_tree["database"]["set_user_state"], 
                            [chat_id, level, funnel, params, level, funnel, params])

def get_user_state(chat_id):
    sql_result = db_helper.do_sql(
        bot_tree["database"]["get_user_state"], [chat_id])
    if len(sql_result) == 0:
        return None
    if len (sql_result[0]) != 3:
        return None
    state = [sql_result[0][0], sql_result[0][1], sql_result[0][2]]
    return state

async def select_date(chat_id):
    state = get_user_state(chat_id)
    sql =  "SELECT * FROM client_order WHERE client_id = %s"
    sql_result = db_helper.do_sql(sql, [chat_id])
    print (sql_result)
    if len(sql_result) > 0:
        sql_result = db_helper.do_sql(sql, [chat_id])
        text = "Вкажіть дату й час, коли хочете отримати замовлення.\nМінімальний термін замовлення:\nТорт/чизкейк - 6-7 днів\nКапкейки - 4-5 днів"
    else:
        #text = "Спершу оберіть смаколики для замовлення, щоб було, що оформляти 😊"
        #set_user_state(chat_id, [None, None, None])
        return
    await bot.send_message(chat_id, text)          

async def finish_order(chat_id):
    sql = "DELETE FROM client_order WHERE client_id = %s"
    db_helper.do_sql(sql, [chat_id])
    text = "Замовлення прийнято! З вами скоро зв'яжеться кондитер, щоб все детально обговорити" 
    await bot.send_message(chat_id, text)
    text = "Хочете смаколиків 🧞?"
    inline_buttons = [
                        [ ["Замовити смаколики", "order"] ],
                        [ ["Інфо", "info_in_telegram"] ]
                     ]
    inline_keyboard = types.InlineKeyboardMarkup()
    rows = inline_buttons
    for row in rows:
        buttons_row = []
        for button in row:
            buttons_row.append(types.InlineKeyboardButton(
                text=button[0], callback_data=button[1]))
        inline_keyboard.row(*buttons_row)
    markup = inline_keyboard
    await bot.send_message(chat_id, text, reply_markup=markup)

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

    sql = "INSERT INTO client_order VALUES(%s, %s)"
    db_helper.do_sql(sql, [chat_id, text])
    text+="\nЧудово! Ви замовите ще щось чи оформите те, що є?"

    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(types.InlineKeyboardButton('Замовити ще', callback_data='order'))
    inline_kb.add(types.InlineKeyboardButton('Оформити', callback_data='order_info'))

    await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=inline_kb)
    

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