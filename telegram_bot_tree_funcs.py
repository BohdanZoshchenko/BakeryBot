# this module is NOT UNIVERSAL for different bots
from modules import *
from settings import *
from datetime import datetime
import pytz
from pytz import timezone


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
    if len(sql_result[0]) != 3:
        return None
    state = [sql_result[0][0], sql_result[0][1], sql_result[0][2]]
    return state


async def form_order(chat_id):
    state = get_user_state(chat_id)
    sql = "SELECT * FROM client_order WHERE client_id = %s AND sent = FALSE"
    sql_result = db_helper.do_sql(sql, [chat_id])
    if len(sql_result) > 0:
        sum = 0.0
        desc = ""
        for row in sql_result:
            sum += row[3]
            desc += row[2] + "\n"
        sum_text = desc + "*Ваше замовлення на суму " + \
            price_format(sum) + " ГРН. + декор*\n"
        text = sum_text + "*ОБОВ'ЯЗКОВО* вкажіть дату й час, коли хочете отримати замовлення.\nМінімальний термін замовлення:\nТорт/чизкейк - 6-7 днів\nКапкейки - 4-5 днів"
        inline_buttons = [
            [["Скасувати замовлення", "cancel_orders"]]
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
        await bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")


async def save_date(chat_id, param):
    sql = "INSERT INTO client_data (chat_id, datetime) VALUES(%s,%s) ON CONFLICT (chat_id) DO UPDATE SET datetime = %s"
    db_helper.do_sql(sql, [chat_id, param, param])


async def save_phone(chat_id, param):
    sql = "UPDATE client_data SET phone = %s WHERE chat_id = %s"
    db_helper.do_sql(sql, [param, chat_id])


async def finish_order(chat_id, param, message):
    sql = "UPDATE client_data SET name = %s WHERE chat_id = %s"
    db_helper.do_sql(sql, [param, chat_id])

    text = "Замовлення прийнято! З вами скоро зв'яжеться кондитер, щоб все детально обговорити"
    await bot.send_message(chat_id, text)
    text = "Хочете смаколиків 🧞?"
    inline_buttons = [
        [["Замовити смаколики", "order"]],
        [["Інфо", "info_in_telegram"]]
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

async def admin_orders(chat_id, param, page_n = 1, page_size = 5):
    if param is not None:
        page_n = int(param[0])
    
    sql = "SELECT description, price FROM client_order WHERE sent = TRUE ORDER BY ID DESC LIMIT %s OFFSET %s"
    count = page_size
    start = (page_n-1) * page_size
    orders = db_helper.do_sql(sql,[count, start])
    for o in orders:
        text = o[0]
        await bot.send_message(chat_id, text, parse_mode="Markdown")
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(
            text="До новіших", callback_data="show_orders_page%" + str(page_n-1))
    btn2 = types.InlineKeyboardButton(
            text="До старіших", callback_data="show_orders_page%" + str(page_n+1))
    btns = []

    sql = "SELECT ID FROM client_order ORDER BY ID DESC"
    pages_count = len(db_helper.do_sql(sql))/page_size
    if page_n > 1:
        btns.append(btn1)
    if page_n < pages_count:
        btns.append(btn2)
    markup.row(*btns)
    markup.row(types.InlineKeyboardButton(
        'Назад', callback_data="admin_show_categories"))
    text = "Опції"
    await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)


async def send_orders_to_admin(client_id, message:types.Message):
    sql = "SELECT description, price FROM client_order WHERE client_id = %s AND sent = FALSE"
    orders = db_helper.do_sql(sql, [client_id])
    sum_order = ""
    sum = 0.0
    for row in orders:
        sum_order += row[0] + "\n"
        sum += row[1]
    sum_order += "*Всього на суму: " + \
        price_format(sum) + " ГРН" + " + декор*\n*Telegram:* @" + \
        message.chat.username
    sql = "SELECT * FROM client_data WHERE chat_id = %s"
    sql_result = db_helper.do_sql(sql, [client_id])
    row = sql_result[0]
    sum_order += "\n*Вказаний час:* " + sql_result[0][1]
    sum_order += "\n*Вказаний телефон:* " + sql_result[0][2]
    sum_order += "\n*Вказане ім'я:* " + sql_result[0][3]

    time = message.date
    
    tz = "Europe/Kiev"
    local_time=time.astimezone(tz)
    sum_order += "\n*Коли зроблено замовлення:* " + str(local_time)
    sql = "UPDATE client_data SET price = %s, order_desc = %s WHERE chat_id = %s"

    db_helper.do_sql(sql, [sum, sum_order, client_id])
    sql = "SELECT user_id FROM admin"
    admins = db_helper.do_sql(sql, [])


    sql = "DELETE FROM client_order WHERE client_id = %s AND sent = FALSE"
    db_helper.do_sql(sql, [client_id])
    sql = "INSERT INTO client_order (client_id, description, price, sent) VALUES(%s, %s, %s, TRUE)"
    db_helper.do_sql(sql, [client_id, sum_order, price_format(sum)])

    for row in admins:
        text = sum_order
        print(text)
        await bot.send_message(row[0], "Нове замовлення:\n" + text, parse_mode="Markdown")

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
            emoji + ' ' + item[0]+' '+str(item[1]) + ' ' + 'ГРН/'+dim, callback_data='show_item%' + item[0])
        markup.add(button)
    await bot.send_message(chat_id, "Обирайте 🧐", reply_markup=markup)


async def show_single_item(chat_id, param, sql_result):
    item = sql_result[0]
    category = item[4]
    text = '*'+param[0]+'*\n'
    text += str(item[1])+"\n"  # description
    text += str("Ціна: " + str(item[3]) + " ГРН/" +
                dims[category]+" + за декор окремо") + "\n"  # price
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
    sql_res = db_helper.do_sql(
        'SELECT category FROM item WHERE name=%s', [name])
    category = sql_res[0][0]
    if category == "Торти":
        text = "*"+name + \
            "*\nЯку вагу бажаєте (від 2 до 102 кілограмів 😊)? Наприклад, 3.25"
    elif category == 'Капкейки':
        text = "*"+name + \
            "*\nЯку кількість бажаєте (від 6 до 106 штук 😊)? Наприклад, 10"
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

    text = "*" + name+"\n"
    text += str(mass) + " "+dims[category]+" x " + str(price) + " = "
    text += str(sum) + " ГРН + за декор окремо*"

    sql = "INSERT INTO client_order (client_id, description, price) VALUES(%s, %s, %s)"
    db_helper.do_sql(sql, [chat_id, text, float(sum)])
    text += "\nЧудово! Ви замовите ще щось чи оформите те, що є?"

    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(types.InlineKeyboardButton(
        'Замовити ще', callback_data='order'))
    inline_kb.add(types.InlineKeyboardButton(
        'Оформити', callback_data='order_info'))

    await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=inline_kb)


async def cancel_orders(chat_id):
    sql = "DELETE FROM client_order WHERE client_id = %s AND sent = FALSE"
    db_helper.do_sql(sql, [chat_id])
    text = "Ваші останні замовлення скасовано."
    inline_buttons = [
        [["Замовити смаколики", "order"]],
        [["Інфо", "info_in_telegram"]]
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

async def save_admin(chat_id):
    sql = "SELECT user_id FROM admin WHERE user_id = %s"
    res = db_helper.do_sql(sql, [chat_id])
    add_to_db = True
    for r in res:
        if r[0] == chat_id:
            add_to_db = False
            break
    if add_to_db:
        sql = "INSERT INTO admin (user_id) VALUES(%s)"
        db_helper.do_sql(sql, [chat_id])
    await admin_categories(chat_id)

async def admin_categories(chat_id):
    sql_result = db_helper.do_sql("SELECT category FROM item")
    categories = []
    inline_buttons = []
    for c in sql_result:
        if c[0] is not None and c[0] not in categories:
            categories.append(c[0])
            inline_buttons.append([[c[0], 'admin_category%'+c[0]]])

    add_categories = ["Торти", "Капкейки"]
    
    for a in add_categories:
        if a is not None and a not in categories:
            inline_buttons.append([[a, 'admin_category%'+a]])
    inline_keyboard = types.InlineKeyboardMarkup()
    rows = inline_buttons
    for row in rows:
        buttons_row = []
        for button in row:
            buttons_row.append(types.InlineKeyboardButton(
                text=button[0], callback_data=button[1]))
        inline_keyboard.row(*buttons_row)
    inline_keyboard.row(*[types.InlineKeyboardButton(
        text="Отримані замовлення", callback_data="admin_show_orders")])
    inline_keyboard.row(*[types.InlineKeyboardButton(
        text="Змінити інфо", callback_data="edit_info")])
    markup = inline_keyboard
    text = "*Режим адміністратора*\nЩоб відкрити режим клієнта, надішліть будь-який текст і натисніть Спробувати"
    await bot.send_message(chat_id, text, reply_markup=markup,  parse_mode="Markdown")


async def admin_show_category(chat_id, param):
    sql = "SELECT name, price FROM item WHERE category=%s ORDER BY price"
    category = param[0]
    emoji = emojis[category]
    dim = dims[category]
    sql_result = db_helper.do_sql(sql, [category])
    items = sql_result
    markup = types.InlineKeyboardMarkup()
    for item in items:
        button = types.InlineKeyboardButton(
            emoji + ' ' + item[0]+' '+str(item[1]) + ' ' + 'ГРН/'+dim, callback_data='admin_show_item%' + item[0])
        markup.add(button)
    markup.row(*[types.InlineKeyboardButton(
        text="Новий виріб", callback_data="admin_add_item%"+category)])
    categories_button = types.InlineKeyboardButton(
        'Назад', callback_data="admin_show_categories")
    markup.add(categories_button)
    await bot.send_message(chat_id, "Обирайте 🧐", reply_markup=markup, parse_mode="Markdown")


async def admin_show_item(chat_id, param):
    sql = "SELECT * FROM item WHERE name=%s"
    sql_result = db_helper.do_sql(sql, [param[0]])
    item = sql_result[0]
    category = item[4]
    text = '*'+param[0]+'*\n'
    text += str(item[1])+"\n"  # description
    text += str("Ціна: " + str(item[3]) + " ГРН/" +
                dims[category]+" + за декор окремо") + "\n"  # price
    text += "Унікальний декор за вашими побажаннями" + "\n"
    if category == "Торти":
        text += "Мінімальна вага до замовлення 2 кг"
    elif category == 'Капкейки':
        text += "Мінімальна кількість до замовлення 6 шт"
    markup = types.InlineKeyboardMarkup()
    name_button = types.InlineKeyboardButton(
        'Змінити назву', callback_data="admin_change_name"+'%' + param[0])
    desc_button = types.InlineKeyboardButton(
        'Змінити опис', callback_data="admin_change_desc"+'%' + param[0])
    price_button = types.InlineKeyboardButton(
        'Змінити ціну', callback_data="admin_change_price"+'%' + param[0])
    photo_button = types.InlineKeyboardButton(
        'Змінити фото', callback_data="admin_change_photo"+'%' + param[0])
    delete_button = types.InlineKeyboardButton(
        'Видалити виріб', callback_data="admin_delete_item"+'%' + param[0])
    categories_button = types.InlineKeyboardButton(
        'Назад', callback_data="admin_show_categories")
    #markup.row(info_button, back_button)
    markup.row(name_button, desc_button)
    markup.row(price_button, photo_button)
    markup.row(delete_button)
    markup.row(categories_button)
    await bot.send_photo(chat_id, item[2], caption=text, parse_mode="Markdown", reply_markup=markup)

async def admin_change_name(chat_id, param, state):
    params = state[2]
    name = params[0]
    new_name = param
    sql = "SELECT * FROM item WHERE name=%s"
    count = len(db_helper.do_sql(sql, [name]))
    if count == 0:
        await bot.send_message(chat_id, "Цю назву вже міняли.", parse_mode="Markdown")
        return
    count = len(db_helper.do_sql(sql, [new_name]))
    if count == 0:
        sql = "UPDATE item SET name = %s WHERE name = %s"
        db_helper.do_sql(sql, [new_name, name])

        await admin_show_item(chat_id, [new_name])
    else:
        await bot.send_message(chat_id, "Така назва вже є, нічого не змінено.", parse_mode="Markdown")
        await admin_show_item(chat_id, [name])


async def admin_change_desc(chat_id, param, state):
    params = state[2]
    name = params[0]
    new_desc = param
    sql = "SELECT * FROM item WHERE name=%s"
    count = len(db_helper.do_sql(sql, [name]))
    if count == 0:
        await bot.send_message(chat_id, "Ця назва вже неактуальна, тому тут не вийде нічого міняти.", parse_mode="Markdown")
    else:
        sql = "UPDATE item SET description = %s WHERE name = %s"
        db_helper.do_sql(sql, [new_desc, name])

        await admin_show_item(chat_id, [name])


async def admin_change_price(chat_id, param, state):
    params = state[2]
    name = params[0]
    new_price = param
    sql = "SELECT * FROM item WHERE name=%s"
    count = len(db_helper.do_sql(sql, [name]))
    if count == 0:
        await bot.send_message(chat_id, "Ця назва вже неактуальна, тому тут не вийде нічого міняти.", parse_mode="Markdown")
    else:
        sql = "UPDATE item SET price = %s WHERE name = %s"
        db_helper.do_sql(sql, [new_price, name])

        await admin_show_item(chat_id, [name])


async def admin_change_photo(chat_id, param, state):
    params = state[2]
    name = params[0]
    photo = param

    file_info = await bot.get_file(photo[len(photo) - 1].file_id)
    new_photo = (await bot.download_file(file_info.file_path)).read()

    """photoArr = []
    for p in photo: 
        file_info = await bot.get_file(p.file_id)
        downloaded = (await bot.download_file(file_info.file_path)).read()
        photoArr.append(downloaded)
    
    new_photo = photoArr
    """
    

    """
    file_id = photo[-1].file_id
    file = await bot.get_file(file_id)
    new_photo = await bot.download_file(file.file_path)
    """
    sql = "SELECT * FROM item WHERE name=%s"
    count = len(db_helper.do_sql(sql, [name]))
    if count == 0:
        await bot.send_message(chat_id, "Ця назва вже неактуальна, тому тут не вийде нічого міняти.", parse_mode="Markdown")
    else:
        sql = "UPDATE item SET photo = %s WHERE name = %s"

        db_helper.do_sql(sql, [new_photo, name])

        await admin_show_item(chat_id, [name])

async def admin_save_new_item(chat_id, param, state):
    params = state[2]
    name = params[1]

    while len(db_helper.do_sql("SELECT * FROM item WHERE name=%s", [name])) > 0:
        name += "-2"
        

    sql = "INSERT INTO item VALUES(%s,%s,%s,%s,%s)"

    file_info = await bot.get_file(param[len(param) - 1].file_id)
    photo = (await bot.download_file(file_info.file_path)).read()


    category = params[0]
    desc = params[2]
    price = float(params[3])

    db_helper.do_sql(sql, [name, desc, photo, price, category])
    await admin_show_item(chat_id, [name])

async def admin_delete_item(chat_id, param):
    param = param[0]
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(
        text='Ні', callback_data="admin_show_categories")
    markup.add(button)
    button = types.InlineKeyboardButton(
        text='Так', callback_data="admin_delete_item_sure%" + param)
    markup.add(button)
    await bot.send_message(chat_id, "Ви певні, що хочете видалити " + param+"?", reply_markup=markup)

async def admin_delete_item_sure(chat_id, param):
    param = param[0]
    db_helper.do_sql("DELETE FROM item WHERE name = %s", [param])
    await bot.send_message(chat_id, param + " видалено.")
    await admin_categories(chat_id)

async def show_info(chat_id):
    text = db_helper.do_sql("SELECT description FROM info")

    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(
        text='Назад', callback_data="new_greeting")
    markup.add(button)
    if len(text) > 0:
        if text[0][0]!='':
            t = text[0][0]
        else:
            t = "Немає інфо"
    else:
        db_helper.do_sql("INSERT INTO info (description) VALUES('')")
        t = "Немає інфо"
    await bot.send_message(chat_id, t, reply_markup=markup)

async def change_info_start(chat_id):
    text = db_helper.do_sql("SELECT description FROM info")
    print(text)
    if len(text) > 0:
        if text[0][0]!='':
            await bot.send_message(chat_id, text[0][0])
    else:
        db_helper.do_sql("INSERT INTO info (description) VALUES('')")

    text = "Напишіть нове інфо"

    await bot.send_message(chat_id, text)

async def change_info_end(chat_id, param):
    db_helper.do_sql("UPDATE info SET description = %s WHERE description <> %s", [param, param])

    text = "Інфо змінено"

    await bot.send_message(chat_id, text)
    await admin_categories(chat_id)

emojis = {'Капкейки': '🧁', 'Торти': '🍰'}
dims = {'Капкейки': 'ШТ', 'Торти': 'КГ'}
