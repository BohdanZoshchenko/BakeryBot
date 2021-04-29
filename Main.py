# TODO   розділити торти капкейки(мін замовлення 6 штук) тощо, заборонити додавати товар з одною назвою, не давати базі ламатися
# TODO   заблокувати спроби додавати товар з однаковою назвою
# TODO   ЗАДІЗЕЙБЛИТИ юзер відповіді в адмінці

import os
import logging
from flask import Flask, request
from item import Item
from logging import ERROR
from category import Category
import telebot
from telebot import types
import feedparser
import parameters
import orders_control
from dbhelper import DBHelper




bot = telebot.TeleBot(parameters.TOKEN)
db = DBHelper()



###******USER***###

@bot.message_handler(commands=['start', 'help'])
def start(message):
    if not parameters.admin:
        m = message
        start_msg(message=m) 

def start_msg(message = None, call=None):
    id = get_chat_id(msg=message, callback=call)
    markup = keyb([ ["Замовити смаколики", "show_list"] , ["Інфо", "info"] ])
    bot.send_message(id, text="Привіт, я бот кондитерської Mari_Ko BAKERY CLUB! Чого бажаєте?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def get_call(call):
    if not parameters.admin:
        if call.data == "skip_decor_photo":
            decor_photo(callback=call)
        #if call.data == "order_begin":
        #    show_item(callback=call)
        elif call.data == "show_list":
            show_list(callback=call)
        elif "show_item_" in call.data:
            name = call.data.replace("show_item_","")
            show_item(callback=call, item_name=name)
        elif "order_this_" in call.data:
            make_order(call)
        elif call.data == 'start':
            c = call
            start_msg(call=c)
        #elif "user_items_page_" in call.data:
         #   number = int(call.data.replace("user_items_page_", ''))
          #  show_item(callback=call, category_number=number)
        elif call.data == "info":
            show_info(call)
    else:
        if 'update_item_' in call.data:
            name = int(str(call.data).replace('update_item_', ''))
            parameters.category_from_db = db.get_item_by_name_from_db(name)

            #add_category_position_menu(callback=call)

def make_order(callback):
    print("ORDER")
    item_name = callback.data.replace("order_this_", "")
    client = callback.from_user
    print(client.id)
    orders_control.orders[client.id] = [item_name, None]
    bot.send_message(chat_id=callback.message.chat.id, text="Ок. Яку вагу бажаєте (від 2 кг)? Наприклад, 3.25")

    parameters.mode = "type_kg"
   
def type_kg(message):
    def exc():
        bot.send_message(chat_id=message.chat.id, text="Не розумію:(.\nОк. Яку вагу бажаєте (від 2 кг)? Наприклад, 3.25")
    kg = 2
    try:
        txt = message.text
        txt = txt.replace(",",".")
        kg = round(abs(float(txt)), 3)
        print(kg)
        if (kg >= 2 and kg <= 100):
            client = message.from_user
            
            #print(client.id)
            #print("minus first")
            item_name = orders_control.orders[client.id][0]
            #print("zero")
            item_from_db = db.get_item_by_name_from_db(item_name)
           
            p = item_from_db[3]
            
            orders_control.orders[client.id][0] += "\n" + str(kg) + " кг * " + str(p) + " = " + str(round(kg*p, 2)) + " ГРН"
            
            bot.send_message(chat_id=message.chat.id, text=orders_control.orders[client.id][0]+"\nЧудово. Тепер напишіть побажання щодо смаколика. Наприклад, про начинку і декор або дату бронювання")
            
            parameters.mode = "type_wishes"
        else:
            print("else")
            exc()
    except:
        exc()

def wishes_filling_decor(message):
    markup = keyb([["Пропустити", 'skip_decor_photo']])
    client = message.from_user

    orders_control.orders[client.id][0] += "\n" + "Побажання щодо декору:\n" + message.text
    bot.send_message(chat_id=message.chat.id, reply_markup=markup, text=orders_control.orders[client.id][0]+"\nНасамкінець, можете надіслати 1 зображення, за яким можна зробити декор. А можете пропустити цей крок.")
    
    parameters.mode = "decor_photo"

def decor_photo(callback = None, message = None):
    if not parameters.mode == "decor_photo":
        return
    id = get_chat_id(message, callback)
    client = None
    t = ""
    if message != None:
        client = message.from_user
        fileID = message.photo[-1].file_id

        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        orders_control.orders[client.id][1] = downloaded_file
        t = "Прийнято 1 зображення.\n"
    elif callback != None:
        client = callback.from_user

    db.add_order(client.id)
    parameters.mode = None
    markup=keyb([ ['Продовжити', 'start'] ])

    bot.send_message(chat_id=id, reply_markup=markup, text=t+orders_control.orders[client.id][0]+"\nЗамовлення прийнято. Тепер почекайте, доки з вами зв'яжеться людина для уточнення деталей")

def show_list(callback):
    items = db.get_each_item_from_db()
    buttons = []
    for item in items:
        buttons.append( [item[0]+" "+str(item[3])+" ГРН/КГ", "show_item_" + item[0]] )
    
    buttons.append(["Інфо", "info"])
    markup = keyb(buttons)
    bot.send_message(chat_id=callback.message.chat.id, text="Обирайте:)", reply_markup=markup)

def show_item(callback, item_name):
    print("ok")
    item = db.get_item_by_name_from_db(name=item_name)
    #categories = db.get_each_category_from_db()

    #curr_category = categories[category_number]
    #price = curr_category[0]
    #items = db.get_items_by_price_from_db(price)
    #item = items[item_number]

    text = ""
    text += str(item[0])+"\n" #name
    text += str(item[1])+"\n" #description
    text += str("Ціна: " + str(item[3]) + " ГРН/КГ + за декор окремо") + "\n"#price
    text += "Унікальний декор за вашими побажаннями" + "\n"
    text += "Мінімальна вага до замовлення 2 кг"
    #markup = None
    #if len(categories)>category_number+1:
    markup = keyb([ ["Замовити", "order_this_" + item[0]], ["Вибрати щось інше", "show_list"], ["Інфо", "info"] ])
        #markup=keyb([  ["➡️ далі: від " + str(categories[category_number+1][0]) + " грн./кг", "user_items_page_" + str(category_number+1) ]  ])
        #bot.send_message(chat_id=callback.message.chat.id, text=item[0]) #name
        #bot.send_message(chat_id=callback.message.chat.id, text=item[1]) #description
    bot.send_photo(chat_id=callback.message.chat.id, photo=item[2], caption=text, reply_markup=markup) #photo
        #bot.send_message(chat_id=callback.message.chat.id, text="Ціна: " + str(item[3]) + " грн./кг + за декор окремо.", reply_markup=markup) #price

def show_info(call):
    info = 'З додаткових питань, пишіть кондитерці Марії @MariaYav'
    markup = keyb([ ['Замовити смаколики', "show_list"] ])
    bot.send_message(chat_id=call.message.chat.id, text=info, reply_markup=markup)

####***ADMIN***####

def get_chat_id(msg, callback):
    id = None
    if msg != None:
        id = msg.chat.id
    elif callback != None:
        id = callback.message.chat.id
    return id


def is_password_valid(password):
    has8symbols = False
    containsDigit = False
    containsUpper = False
    containsLower = False
    noSpaces = True

    if len(password) >= 8:
        has8symbols = True

    for ch in password:
        if ch.isdigit():
            containsDigit = True
        elif ch.isupper():
            containsUpper = True
        elif ch.islower():
            containsLower = True
        elif ch == ' ':
            noSpaces = False

    err_result = "Пароль не досить сильний. Спробуйте ще. Ось чому пароль слабкий:"
    if not has8symbols:
        err_result += "\nВи ввели менше 8 символів."
    if not containsDigit:
        err_result += "\nВи не ввели жодної цифри."
    if not containsUpper:
        err_result += "\nВи не ввели жодної великої літери."
    if not containsLower:
        err_result += "\nВи не ввели жодної маленької літери."
    if not noSpaces:
        err_result += "\nВи ввели пробіл."
    if has8symbols and containsDigit and containsUpper and containsLower and noSpaces:
        err_result = "OK"
    return err_result


def add_category(msg=None, callback=None):
    id = get_chat_id(msg, callback)
    parameters.mode = "add_category_price"
    keyboard = simple_keyb(['До меню керування'])
    bot.send_message(chat_id=id, reply_markup=keyboard,
                     text="Ок. Напишіть ціну нової категорії в гривнях (без декору). Просто число.")


def add_position(msg=None, callback=None):
    id = get_chat_id(msg, callback)
    p = None
    if parameters.current_category == None:
        p = parameters.category_from_db[0]
    else:
        p = parameters.current_category.price
    item = Item(price=p, name=msg.text)
    
    bot.send_message(chat_id=id, text="Чудово! Тепер давайте дамо короткий опис до " + item.name)
    parameters.mode = "add_item_description"
    parameters.current_item = item

def items_menu_admin(msg=None, callback=None):
    id = get_chat_id(msg, callback)

    #db.add_item("Something", id)
    #keyboard = keyb([[db.get_items(id)[0], '45']])
    """
    keyboard = simple_keyb(['Додати цінову категорію', 'До меню керування'])
    bot.send_message(chat_id=id, reply_markup=keyboard,
                     text="Давайте додамо нову цінову категорію або змінимо стару))")
    categories = db.get_each_category_from_db()
    if len(categories) > 0:
        bot.send_message(chat_id=id, reply_markup=keyboard,
                         text='Список доступних категорій:')
    for cat in categories:
        # , ['Видалити категорію','delete_category_'+str(cat[0])]])
        inline = keyb([['Змінити категорію', 'update_category_'+str(cat[0])]])
        bot.send_message(chat_id=id, reply_markup=inline,
                         text=str(cat[0]) + ' грн./кг + ціна за декор')
    """
    keyboard = simple_keyb(['Додати новий виріб', 'До меню керування'])
    bot.send_message(chat_id=id, reply_markup=keyboard,
                     text="Давайте додамо новий виріб або змінимо старий.")
    items = db.get_each_item_from_db()
    buttons = []

    for item in items:
        """   
        inline = keyb([ ['Змінити назву', 'update_item_name_'+str(item[0])],
        ['Змінити опис', 'update_item_description_'+str(item[0])],
        ['Змінити фото', 'update_item_photo_'+str(item[0])],
        ['Змінити ціну', 'update_price_'+str(item[0])]
        ])
        
        text = ""
        text += str(item[0])+"\n" #name
        text += str(item[1])+"\n" #description
        text += str("Ціна: " + str(item[3]) + " ГРН/КГ + за декор окремо")
        
        bot.send_photo(chat_id=id, reply_markup=inline, photo=item[2],
            caption=text)
        """
        buttons.append( [item[0]+" "+str(item[3])+" ГРН/КГ", "update_item_" + item[0]] )
        
    markup = keyb(buttons)
    if len(items) > 0:
        bot.send_message(chat_id=id, reply_markup=markup,
                         text='Список доступних виробів:')
    
    

def items_menu_user(msg=None, callback=None):
    id = get_chat_id(msg, callback)


def admin_menu(msg=None, callback=None):
    id = get_chat_id(msg, callback)
    #keyboard = keyb([['Оновити дані', 'update_data'],['Оновити інфо', 'update_info'],['Змінити пароль', 'update_password'], ['Вийти з цього меню', 'exit_admin']])
    keyboard = simple_keyb(
        ['Оновити дані', 'Оновити інфо', 'Змінити пароль', 'Вийти з керування ботом'])
    
    bot.send_message(chat_id=id, reply_markup=keyboard,
                     text="Ласкаво прошу до керування чатботом! Тобто мною.\nСюди має доступ лише людина з паролем.\nЩо бажаєте зробити?")
    parameters.admin = True
    parameters.mode = None


def change_password_menu(msg=None, callback=None):
    id = get_chat_id(msg, callback)
    parameters.mode = "change_password"
    kb = simple_keyb(['Ні, не хочу міняти'])
    bot.send_message(chat_id=id, reply_markup=kb, text="Ок, змінюємо пароль. Напишіть мені новий. Він має бути складний - мінімум 8 символів всього, мінімум 1 маленька літера і 1 велика літера, мінімум 1 цифра. Без пробілів.\nПам'ятайте чи зберігайте його в безпеці.")


def add_category_position_menu(msg=None, callback=None):
    print(3)
    id = get_chat_id(msg, callback)
    parameters.mode = 'add_category_position'
    #photo = msg.photo[0].file_id
    #parameters.current_category.photo = photo
    keyboard = simple_keyb(['Пропустити', 'До меню керування'])
    bot.send_message(chat_id=id, reply_markup=keyboard,
                     text='Напишіть назву нової позиції.')

@bot.message_handler(content_types=['photo'])
def handle_command(message):
    if parameters.admin:
        if parameters.mode == "add_item_photo":
            fileID = message.photo[-1].file_id
            file_info = bot.get_file(fileID)
            downloaded_file = bot.download_file(file_info.file_path)
            parameters.current_item.photo = downloaded_file
            db.save_item_to_db(parameters.current_item)
            bot.send_message(chat_id=message.chat.id, text='Ок... Ось ваш смаколик!')
            parameters.mode = 'show_new_item'
            items = db.get_item_from_db(parameters.current_item.price, parameters.current_item.name)
            bot.send_message(chat_id=message.chat.id, text=items[0][0])
            bot.send_photo(chat_id=message.chat.id, photo=items[0][2])
#        if parameters.mode == "add_category_photo":
#            add_category_position_menu(message)
    else:
        if parameters.mode == "decor_photo":
            m = message
            decor_photo(message = m)


@bot.message_handler(content_types=['text'])
def handle_command(message):
    if not parameters.admin:
        if parameters.mode == "type_kg":
            type_kg(message)
        elif parameters.mode == "type_wishes":
            wishes_filling_decor(message)
    if parameters.admin:
        if parameters.mode == "add_item_description":
            parameters.current_item.description = message.text
            bot.send_message(chat_id=message.chat.id, text='Опис додано:) а тепер завантажте смачне фото цього смаколика!')
            parameters.mode = "add_item_photo"
        if parameters.mode == "add_category_position":
            add_position(msg=message)
        elif parameters.mode == "add_category_price":
            if message.text == 'До меню керування':
                admin_menu(msg=message)
                return
            try:
                price = abs(int(message.text))
                cat = Category(price)
                cat.price = price
                parameters.current_category = cat
                db.save_category_to_db(category=parameters.current_category)
                parameters.mode = "add_category_position"

                keyboard = simple_keyb(['Пропустити', 'До меню керування'])
                bot.send_message(chat_id=message.chat.id, reply_markup=keyboard,
                                 text='Клас! А зараз можна додати нові позиції до категорії.\nНапишіть назву нової позиції.')

                #bot.send_message(chat_id=message.chat.id, reply_markup=keyboard, text = 'Чудово! Тепер надішліть смачне фото, яке презентуватиме категорію) Втім, цей крок можна зробити пізніше')
            except BaseException as error:
                if 'duplicate key value violates unique constraint' in str(error):
                    bot.send_message(
                        chat_id=message.chat.id, text='А така категорія вже є. Ви можете змінити її.')
                    return
                elif 'invalid literal for int()' in str(error):
                    bot.send_message(
                        chat_id=message.chat.id, text='Будь ласка, введіть ціну у гривнях (без декору), і без копійок:). Просто число.')
                    return
                else:
                    bot.send_message(
                        chat_id=message.chat.id, text='Дивно, якась невідома науці помилка... Можете спробувати ще або звернутися до розробника.')
                    return
        elif parameters.mode == "change_password":
            if message.text == 'Ні, не хочу міняти':
                parameters.mode = None
                bot.send_message(chat_id=message.chat.id, text="Гаразд")
                admin_menu(msg=message)
                return
            result = is_password_valid(message.text)
            if result == "OK":
                parameters.admin_password = message.text
                parameters.mode = None
                bot.send_message(chat_id=message.chat.id,
                                 text="Пароль змінено!")
                admin_menu(msg=message)
            else:
                bot.send_message(chat_id=message.chat.id, text=result)
                change_password_menu(msg=message)
        elif message.text == 'Вийти з керування ботом':
            bot.send_message(chat_id=message.chat.id,
                             text="Ок, повертаюся в звичайний режим)")
            parameters.admin = False
            m = message
            start_msg(message=m)
        elif message.text == 'Змінити пароль':
            change_password_menu(msg=message)
        elif message.text == "Оновити дані":
            items_menu_admin(msg=message)
        elif message.text == "Додати цінову категорію":
            add_category(msg=message)
        elif message.text == 'До меню керування':
            admin_menu(msg=message)
        # else:
           # bot.send_message(chat_id=message.chat.id, text="Не зрозумів. Давайте спробуємо ще раз))")
           # admin_menu(msg=message)
    elif message.text == parameters.admin_password:
        admin_menu(msg=message)


def keyb(items):
    markup = types.InlineKeyboardMarkup()
    for i in items:
        markup.add(types.InlineKeyboardButton(text=i[0], callback_data=i[1]))
    return markup


def simple_keyb(items):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for i in items:
        markup.row(i)
    markup.resize_keyboard = True
    return markup


FEED_URL = 'https://widget.stagram.com/rss/n/mari_ko_bakeryclub'


def feed_parser():
    NewsFeed = {'Inst': 'https://widget.stagram.com/rss/n/mari_ko_bakeryclub'}
    message = dict()
    for key in NewsFeed.keys():
        current_news = feedparser.parse(NewsFeed[key]).entries[0]
        message[key] = current_news.title + '\n' + current_news.link
    return message


i450 = [
    ["Ванільно-ягідний", '1'],
    ["Ягідно-муссовий", '2'],
    ["Шоколадно-трюфельний", '3'],
    ["➡️ 500 грн./кг", '4']
]


i500 = [
    'Пряна вишня', 'Горіховий', 'Червоний оксамит', 'Снікерс', [
        '⬅️ 450 грн./кг', '➡️ 550 грн./кг']
]


kb_450 = keyb(items=i450)

#kb_500 = keyb(items=i500)

# handle commands, /start


#@bot.message_handler(commands=['start', 'help'])
#def handle_command(message):
#    bot.send_message(chat_id=message.chat.id,
 #                    reply_markup=kb_450, text="450 грн./кг")
    #bot.send_message(message.chat.id, text="Привіт, я бот пекарні Марії Чернієнко! Чого бажаєте?😃😃", reply_markup=markup)

# handle all messages, echo response back to users
# @bot.message_handler(func=lambda message: True)
# def handle_all_message(message):
#	bot.reply_to(message, message.text)

# @bot.message_handler(commands=['read_rss'])
# def read_rss(message):
#    post = feed_parser()
#    bot.send_message(message.chat.id, 'Новая информация на выбранных площадках:')
#   for key in post.keys():
#        bot.send_message(message.chat.id, key + '\n' + post[key])


if "HEROKU" in list(os.environ.keys()):
    logger = telebot.logger
    telebot.logger.setLevel(logging.INFO)
    
    server = Flask(__name__)
    @server.route('/'+parameters.TOKEN, methods=['POST'])
    def getMessage():
        json_string = request.stream.read().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    
    @server.route("/")
    def webhook():
        bot.remove_webhook()
        bot.set_webhook(url="https://bakerybotmariko.herokuapp.com/"+parameters.TOKEN)
        return "?", 200
    from waitress import serve
    serve(server, host="0.0.0.0", port=os.environ.get('PORT', 33507))

else:       
    bot.remove_webhook()
    bot.polling(none_stop=True)
