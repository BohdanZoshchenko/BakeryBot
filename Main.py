import os
from flask import Flask, request
import logging
from logging import ERROR
from category import Category

import telebot

from telebot import types
import feedparser
import parameters
from dbhelper import DBHelper

bot = telebot.TeleBot(parameters.TOKEN)
db = DBHelper()

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

def add_category(msg = None, callback = None):
    id = get_chat_id(msg, callback)
    parameters.mode_in_admin = "add_category_price"
    keyboard = simple_keyb(['До керування ботом'])
    bot.send_message(chat_id=id, reply_markup=keyboard, text="Ок. Напишіть ціну нової категорії в гривнях (без декору). Просто число.")

def add_position(msg = None, callback = None):
    id = get_chat_id(msg, callback)
    bot.send_message(chat_id=id, text="Ок. Напишіть назву нової позиції")

def items_menu_admin(msg = None, callback = None):
    id = get_chat_id(msg, callback)

    #db.add_item("Something", id)
    #keyboard = keyb([[db.get_items(id)[0], '45']])
    keyboard = simple_keyb(['Додати цінову категорію', 'До керування ботом'])
    bot.send_message(chat_id=id, reply_markup=keyboard, text="Давайте додамо нову цінову категорію або змінимо стару))")
    categories = db.get_each_category_from_db()
    if len(categories) > 0:
        bot.send_message(chat_id=id, reply_markup=keyboard, text='Список доступних категорій:')
    for cat in categories:
        inline = keyb([['Змінити категорію', 'update_category_'+str(cat[0])]], ['Видалити категорію','delete_category_'+str(cat[0])])
        bot.send_message(chat_id=id, reply_markup=inline, text=str(cat[0]) + ' грн./кг + ціна за декор')

def items_menu_user(msg = None, callback = None):
    id = get_chat_id(msg, callback)


def admin_menu(msg = None, callback = None):
    id = get_chat_id(msg, callback)
    #keyboard = keyb([['Оновити дані', 'update_data'],['Оновити інфо', 'update_info'],['Змінити пароль', 'update_password'], ['Вийти з цього меню', 'exit_admin']])
    keyboard = simple_keyb(['Оновити дані','Оновити інфо','Змінити пароль', 'Вийти з керування ботом'])
    bot.send_message(chat_id=id, reply_markup=keyboard, text="Ласкаво прошу до керування чатботом! Тобто мною.\nСюди має доступ лише людина з паролем.\nЩо бажаєте зробити?")
    parameters.admin = True
    parameters.mode_in_admin = None

def change_password_menu(msg=None, callback=None):
    id = get_chat_id(msg, callback)
    parameters.mode_in_admin = "change_password"
    kb = simple_keyb(['Ні, не хочу міняти'])
    bot.send_message(chat_id=id, reply_markup=kb, text="Ок, змінюємо пароль. Напишіть мені новий. Він має бути складний - мінімум 8 символів всього, мінімум 1 маленька літера і 1 велика літера, мінімум 1 цифра. Без пробілів.\nПам'ятайте чи зберігайте його в безпеці.")

def add_category_position_menu(msg=None, callback=None):
    print(3)
    id = get_chat_id(msg, callback)
    parameters.mode_in_admin = 'add_category_position'
    #photo = msg.photo[0].file_id
    #parameters.current_category.photo = photo
    keyboard = simple_keyb(['Пропустити', 'До керування ботом'])
    bot.send_message(chat_id=id, reply_markup=keyboard, text = 'Клас! А зараз можна додати нові позиції до категорії.')


@bot.message_handler(content_types=['photo'])
def handle_command(message):
    if parameters.admin:
        print(1)
        if parameters.mode_in_admin == "add_category_photo":
            print(2)
            add_category_position_menu(message)

@bot.message_handler(content_types=['text'])
def handle_command(message):
    if parameters.admin:
        if parameters.mode_in_admin == "add_category_price":
            if message.text == 'До керування ботом':
                admin_menu(msg=message)
                return
            try:
                price = int(message.text)
                cat = Category(price)
                cat.price = price
                parameters.current_category = cat
                db.save_category_to_db(category=parameters.current_category)
                parameters.mode_in_admin = "add_category_position"

                keyboard = simple_keyb(['Пропустити', 'До керування ботом'])
                bot.send_message(chat_id=message.chat.id, reply_markup=keyboard, text = 'Клас! А зараз можна додати нові позиції до категорії.')
            
                #bot.send_message(chat_id=message.chat.id, reply_markup=keyboard, text = 'Чудово! Тепер надішліть смачне фото, яке презентуватиме категорію) Втім, цей крок можна зробити пізніше')
            except BaseException as error:
                print(str(error))
                if 'duplicate key value violates unique constraint' in str(error):
                    bot.send_message(chat_id=message.chat.id, text = 'А така категорія вже є. Ви можете змінити її.')
                    return
                elif 'invalid literal for int()' in str(error):
                    bot.send_message(chat_id=message.chat.id, text = 'Будь ласка, введіть ціну у гривнях (без декору), і без копійок:). Просто число.')
                    return
                else:
                    bot.send_message(chat_id=message.chat.id, text = 'Дивно, якась невідома науці помилка... Можете спробувати ще або звернутися до розробника.')
                    return
        elif parameters.mode_in_admin == "change_password":
            if message.text == 'Ні, не хочу міняти':
                parameters.mode_in_admin = None
                bot.send_message(chat_id=message.chat.id, text="Гаразд")
                admin_menu(msg=message)
                return
            result = is_password_valid(message.text)
            if result == "OK":
                parameters.admin_password = message.text
                parameters.mode_in_admin = None
                bot.send_message(chat_id=message.chat.id, text="Пароль змінено!")
                admin_menu(msg=message)
            else:
                bot.send_message(chat_id=message.chat.id, text=result)
                change_password_menu(msg=message)
        elif message.text == 'Вийти з керування ботом':
            bot.send_message(chat_id=message.chat.id, text="Ок, повертаюся в звичайний режим)")
            parameters.admin = False
            bot.send_message(chat_id=message.chat.id, text="Бажаєте замовити смачненьке?")
            bot.send_message(chat_id=message.chat.id, reply_markup=kb_450, text="450 грн./кг")
        elif message.text == 'Змінити пароль':
            change_password_menu(msg=message) 
        elif message.text == "Оновити дані":
            items_menu_admin(msg=message)
        elif message.text == "Додати цінову категорію":
            add_category(msg=message)
        elif message.text == 'До керування ботом':
            admin_menu(msg=message)
        #else:
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
    markup = types.ReplyKeyboardMarkup()
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
    'Пряна вишня', 'Горіховий', 'Червоний оксамит', 'Снікерс', ['⬅️ 450 грн./кг', '➡️ 550 грн./кг'] 
]


kb_450 = keyb(items=i450)

#kb_500 = keyb(items=i500)

# handle commands, /start
@bot.message_handler(commands=['start', 'help'])
def handle_command(message):
    bot.send_message(chat_id=message.chat.id, reply_markup=kb_450, text="450 грн./кг")
    #bot.send_message(message.chat.id, text="Привіт, я бот пекарні Марії Чернієнко! Чого бажаєте?😃😃", reply_markup=markup)
    
# handle all messages, echo response back to users
#@bot.message_handler(func=lambda message: True)
#def handle_all_message(message):
#	bot.reply_to(message, message.text)

#@bot.message_handler(commands=['read_rss'])
#def read_rss(message):
#    post = feed_parser()
#    bot.send_message(message.chat.id, 'Новая информация на выбранных площадках:')
#   for key in post.keys():
#        bot.send_message(message.chat.id, key + '\n' + post[key])

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if 'delete_category_' in call.data:
        price = int(str(call.data).replace('delete_category_', ''))
        
        
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
    
    server.run(host="0.0.0.0", port=os.environ.get('PORT', 33507))
else:       
    bot.remove_webhook()
    bot.polling(none_stop=True)
