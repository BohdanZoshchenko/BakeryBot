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

async def form_order(chat_id):
    state = get_user_state(chat_id)
    sql =  "SELECT * FROM client_order WHERE client_id = %s AND sent = FALSE"
    sql_result = db_helper.do_sql(sql, [chat_id])
    if len(sql_result) > 0:
        sum = 0.0
        desc = ""
        for row in sql_result:
            sum += row[2]
            desc += row[1] + "\n"
        sum_text = desc + "*Ваше замовлення на суму " + price_format(sum) + " ГРН. + декор*\n"
        text = sum_text + "*ОБОВ'ЯЗКОВО* вкажіть дату й час, коли хочете отримати замовлення.\nМінімальний термін замовлення:\nТорт/чизкейк - 6-7 днів\nКапкейки - 4-5 днів"
        inline_buttons = [
                        [ ["Скасувати замовлення", "cancel_orders"] ]
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
        await bot.send_message(chat_id, text, reply_markup = markup, parse_mode="Markdown") 
             

async def save_date(chat_id, param):
    sql =  "INSERT INTO client_data (chat_id, datetime) VALUES(%s,%s) ON CONFLICT (chat_id) DO UPDATE SET datetime = %s"
    db_helper.do_sql(sql, [chat_id, param, param])

async def save_phone(chat_id, param):
    sql =  "UPDATE client_data SET phone = %s WHERE chat_id = %s"
    db_helper.do_sql(sql, [param, chat_id])

async def finish_order(chat_id, param, message):
    sql =  "UPDATE client_data SET name = %s WHERE chat_id = %s"
    db_helper.do_sql(sql, [param, chat_id])


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

    await send_orders_to_admin(chat_id, message)

async def send_orders_to_admin(client_id, message):
    sql = "SELECT description, price FROM client_order WHERE client_id = %s AND sent = FALSE"
    orders = db_helper.do_sql(sql, [client_id])
    sum_order = ""
    sum = 0.0
    for row in orders:
        sum_order += row[0] + "\n"
        sum += row[1]
    sum_order += "*Всього на суму: " + price_format(sum) + " ГРН" + " + декор*\n*Telegram:* @" + message.chat.username
    sql = "SELECT * FROM client_data WHERE chat_id = %s"
    sql_result = db_helper.do_sql(sql, [client_id])
    row = sql_result[0]
    sum_order += "\n*Вказаний час:* " + sql_result[0][1]
    sum_order += "\n*Вказаний телефон:* " + sql_result[0][2]
    sum_order += "\n*Вказане ім'я:* " + sql_result[0][3]
    sql = "UPDATE client_data SET price = %s, order_desc = %s WHERE chat_id = %s"
    
    db_helper.do_sql(sql, [sum, sum_order, client_id])
    sql = "SELECT user_id FROM admin"
    admins =  db_helper.do_sql(sql, [])
    print("admin len" + str(len(admins)))
    for row in admins:
        print("admin:"+str(row[0]))
        text = sum_order
        await bot.send_message(row[0], text, parse_mode="Markdown")

    print("updating client_order")
    sql = "UPDATE client_order SET sent=TRUE WHERE client_id = %s AND sent = FALSE"
    db_helper.do_sql(sql, [client_id])
    print("updating 2")

async def show_categories(chat_id):
    sql = "SELECT category FROM item"
    result = db_helper.do_sql(sql, [])
    categories = []
    for row in result:
        if row[0] not in categories:
            categories.append(row[0])
    markup = types.InlineKeyboardMarkup()
    for category in categories:
        button = types.InlineKeyboardButton(
            text=str(category), callback_data="show_items%"+category)
        markup.add(button)
    await bot.send_message(chat_id, "Обирайте 🧐", reply_markup=markup)


async def show_items(chat_id, param):
    sql = "SELECT name, price FROM item WHERE category=%s ORDER BY price"
    category = param[0]
    print(param)
    emoji = emojis[category]
    dim = dims[category]
    sql_result = db_helper.do_sql(sql, [category])
    items = sql_result
    markup = types.InlineKeyboardMarkup()
    for item in items:
        button = types.InlineKeyboardButton(
           emoji +' '+ item[0]+' '+str(item[1]) + ' ' + 'ГРН/'+dim, callback_data='show_item%' + item[0])
        markup.add(button)
    await bot.send_message(chat_id, "Обирайте 🧐", reply_markup=markup)


async def show_single_item(chat_id, param, sql_result):
    item = sql_result[0]
    category = item[4]
    text = '*'+param[0]+'*\n'
    text += str(item[1])+"\n" #description
    text += str("Ціна: " + str(item[3]) + " ГРН/" +dims[category]+" + за декор окремо") + "\n"#price
    text += "Унікальний декор за вашими побажаннями" + "\n"
    if category == "Торти":
        text += "Мінімальна вага до замовлення 2 кг"
    elif category == 'Капкейки':
        text += "Мінімальна кількість до замовлення 6 шт"
    markup = types.InlineKeyboardMarkup()
    order_button = types.InlineKeyboardButton(
            'Замовити', callback_data=category+'%' + param[0])
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
    sql_res = db_helper.do_sql('SELECT category FROM item WHERE name=%s', [name])
    category = sql_res[0][0]
    if category == "Торти":
        text ="*"+name+"*\nЯку вагу бажаєте (від 2 до 102 кілограмів 😊)? Наприклад, 3.25"
    elif category == 'Капкейки':
        text ="*"+name+"*\nЯку кількість бажаєте (від 6 до 106 штук 😊)? Наприклад, 10"
    await bot.send_message(chat_id, text, parse_mode="Markdown")

async def order_item_mass(chat_id, state, sql, param):
    level = state[0]
    funnel = state[1]
    params = state[2]
    name = params[0]
    mass = param

    res = db_helper.do_sql(sql, [name])
    price = res[0][0]
    category = res[0][1]
    sum = float(price)*float(mass)
    sum = price_format(sum)

    text = "*"+ name+"\n"
    text+= str(mass) + " "+dims[category]+" x " + str(price) + " = "
    text+= str(sum) + " ГРН + за декор окремо*"

    sql = "INSERT INTO client_order VALUES(%s, %s, %s)"
    db_helper.do_sql(sql, [chat_id, text, float(sum)])
    text+="\nЧудово! Ви замовите ще щось чи оформите те, що є?"

    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(types.InlineKeyboardButton('Замовити ще', callback_data='order'))
    inline_kb.add(types.InlineKeyboardButton('Оформити', callback_data='order_info'))

    await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=inline_kb)
    
async def cancel_orders(chat_id):
    sql = "DELETE FROM client_order WHERE client_id = %s AND sent = FALSE"
    db_helper.do_sql(sql, [chat_id])
    text = "Ваші останні замовлення скасовано."
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

emojis= {'Капкейки' : '🧁', 'Торти':'🍰'}
dims = {'Капкейки' : 'ШТ', 'Торти':'КГ'}
