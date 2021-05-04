import json
import os
import logging
from typing import Dict
from flask import Flask, request
import telebot
from telebot import types
import db

def bot_json_to_obj():
    data = None
    with open("bot.json", "r") as read_file:
        data = json.load(read_file)
    return data

bot_tree = bot_json_to_obj()

bot = telebot.TeleBot(bot_tree["params"]["telegram_token"])  

def handle_goto(chat_id, goto:str, gotos:Dict, simple_buttons):
    if goto == None:
        print("Goto is None")
        return
    text = None
    if "text" in gotos[goto].keys():
        text = gotos[goto]["text"]
    else:
        print(goto + "Goto has no text message")
    if text:
        markup = None
        
        inline_keyboard = None
        if "inline_buttons" in gotos[goto].keys():
            inline_keyboard = types.InlineKeyboardMarkup()
            rows = gotos[goto]["inline_buttons"]
            for row in rows:
                buttons_row = []
                for button in row:
                    buttons_row.append(types.InlineKeyboardButton(text=button[0], callback_data=button[1]))
                inline_keyboard.row(*buttons_row)
            markup = inline_keyboard

        simple_keyboard = None
        if not inline_keyboard and "simple_buttons" in gotos[goto].keys():
            simple_keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            rows = simple_buttons
            for row in rows:
                buttons_row = []
                for button in row:
                    buttons_row.append(types.KeyboardButton(text=button[0]))
                simple_keyboard.row(*buttons_row)
            markup = simple_keyboard
    
        bot.send_message(chat_id, text, reply_markup=markup)
    else:
        print(goto + "Goto has no text")

def handle_unknown_input(chat_id):
    bot.send_message(chat_id, "Я вас не розумію😕 Спробуйте якось інакше.")

@bot.message_handler()
def handle_user_messages_and_simple_buttons(message:types.Message):
    chat_id = message.chat.id

    gotos:Dict = bot_tree["main"]["gotos"]
    commands:Dict = bot_tree["main"]["commands"]
    simple_buttons = bot_tree["main"]["simple_buttons"]

    if message.text != None and message.text != "":
        # command
        if message.text[0] == "/":
            if len(message.text) > 1:
                command = message.text[1:]
                if command in commands.keys():
                    goto = None
                    if "goto" in commands[command].keys():
                        goto = commands[command]["goto"]
                        if goto in gotos.keys():
                            handle_goto(chat_id, goto, gotos, simple_buttons)
                        else:
                            handle_unknown_input(message)
                            print(goto + ":Goto undefined")
                    else:
                        handle_unknown_input(message)
                        print(command + "Command has no goto")
                else:
                    handle_unknown_input(message)
                    print(command + ":Command undefined")
            else:
                handle_unknown_input(message)
                print("No command body")
        elif len(message.text) > 1:
            # simple button
            goto = None
            stop = False
            for row in simple_buttons:
                for button in row:
                    if button[1] in gotos:
                        goto = button[1]
                        stop = True
                        break
                if stop:
                    break
            handle_goto(chat_id, goto, gotos, simple_buttons)
        else:
            handle_unknown_input(message)

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons_callbacks(callback:types.CallbackQuery):
    chat_id = callback.message.chat.id

    gotos:Dict = bot_tree["main"]["gotos"]
    simple_buttons = bot_tree["main"]["simple_buttons"]

    goto = callback.data
    if goto in gotos.keys():
        handle_goto(chat_id, goto, gotos, simple_buttons)
    else:
        handle_unknown_input(chat_id)
        print(goto + ":Goto undefined")

def run():
    if "HEROKU" in list(os.environ.keys()):
        logger = telebot.logger
        telebot.logger.setLevel(logging.INFO)
        
        server = Flask(__name__)
        @server.route('/'+bot_tree["params"]["telegram_token"], methods=['POST'])
        def getMessage():
            json_string = request.stream.read().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return "!", 200
        
        @server.route("/")
        def webhook():
            bot.remove_webhook()
            bot.set_webhook(url=bot_tree["params"]["url"]+bot_tree["params"]["telegram_token"])
            return "?", 200
        from waitress import serve
        serve(server, host="0.0.0.0", port=os.environ.get('PORT', bot_tree["params"]["server_port"]))

    else:       
        bot.remove_webhook()
        bot.polling(none_stop=True)

run()