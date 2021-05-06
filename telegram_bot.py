from modules import *
import funcs_telegram as bot_helper
from inspect import signature

bot = bot_helper.bot
bot_tree = bot_helper.bot_tree

def handle_goto(chat_id, goto:str, gotos:Dict, simple_buttons = None, param = None):
    if goto == None:
        print("Goto is None")
        return

    text = None
    if "text" in gotos[goto].keys():
        text = gotos[goto]["text"]
    else:
        print(goto + ": Goto has no text message")

    markup = None

    if text:
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
        if not inline_keyboard and simple_buttons and "simple_buttons" in gotos[goto].keys():
            simple_keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            rows = simple_buttons
            for row in rows:
                buttons_row = []
                for button in row:
                    buttons_row.append(types.KeyboardButton(text=button[0]))
                simple_keyboard.row(*buttons_row)
            markup = simple_keyboard
    
    sql = None
    sql_result = None
    if "sql" in gotos[goto].keys():
        sql = gotos[goto]["sql"]
        if param:
            p = param
            if isinstance(param, str):
                p = "'"+p+"'"
            sql = sql.replace("%s", p)
        sql_result = db_helper.do_sql(sql)

    if "goto" in gotos[goto].keys():
        handle_goto(chat_id, gotos[goto]["goto"], gotos, simple_buttons, param)

    # This block should be always in the end, before sending message     
    if "func" in gotos[goto].keys():
        func = gotos[goto]["func"]
                
        script = "bot_helper." + func + str(signature(eval("bot_helper." + func)))
        execute_script(script, chat_id, sql, sql_result, param)
                
        return
    # Block end

    # If there was a script, this message will not be sent 
    if text:
        bot.send_message(chat_id, text, reply_markup=markup)

def handle_funnel(chat_id, funnel, level = 0, param = None):
    state = str(level) + "%" + funnel
    if param:
        state += "%" + param
    funnels = bot_tree["main"]["funnels"]
    simple_buttons = bot_tree["main"]["simple_buttons"]
    handle_goto(chat_id, funnel, funnels, simple_buttons, param)
    funnel_branch = funnels[funnel]
    if funnel_branch:
        set_user_state(chat_id, state)

def handle_unknown_input(chat_id):
    handle_goto(chat_id, "unknown_input", gotos=bot_tree["main"])

@bot.message_handler()
def handle_user_messages_and_simple_buttons(message:types.Message):
    chat_id = message.chat.id

    gotos:Dict = bot_tree["main"]["simple_gotos"]
    commands:Dict = bot_tree["main"]["commands"]
    simple_buttons = bot_tree["main"]["simple_buttons"]
    funnels = bot_tree["main"]["funnels"]

    state = get_user_state(chat_id)
    if state:
        play_funnel_level(chat_id, state, message)

    if message.text != None and message.text != "":
        # funnel
        if funnels and message.text in funnels.keys():
            handle_funnel(chat_id, message.text)
            return
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
                            handle_unknown_input(chat_id)
                            print(goto + ":Goto undefined")
                    else:
                        handle_unknown_input(chat_id)
                        print(command + "Command has no goto")
                else:
                    handle_unknown_input(chat_id)
                    print(command + ":Command undefined")
            else:
                handle_unknown_input(chat_id)
                print("No command body")
        else:
            # simple buttons and messages
            goto = None
            for row in simple_buttons:
                for button in row:
                    if button[1] == message.text and button[1] in gotos.keys():
                        print(message.text)
                        goto = button[1]
                        handle_goto(chat_id, goto, gotos, simple_buttons)
                        return
            handle_unknown_input(chat_id)
    else:
        handle_unknown_input(chat_id)

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons_callbacks(callback:types.CallbackQuery): 
    chat_id = callback.message.chat.id

    simple_callbacks:Dict = bot_tree["main"]["simple_callbacks"]
    composite_callbacks:Dict = bot_tree["main"]["composite_callbacks"]
    simple_buttons = bot_tree["main"]["simple_buttons"]
    funnels = bot_tree["main"]["funnels"]

    callb = callback.data
 
    if callb != "":
        state = get_user_state(chat_id)
        if state:
            play_funnel_level(chat_id, state, callback.message)

        # funnel
        if funnels:
            f_keys = funnels.keys()
            for key in f_keys:
                if key in callb and callb[len(key)] == "%":
                    p = callb[len(key)+1:len(callb)]
                    handle_funnel(chat_id, key, param=p)
                    return

    if callb in simple_callbacks.keys():
        handle_goto(chat_id, callb, simple_callbacks, simple_buttons)
        return
    else:
        cc_keys = composite_callbacks.keys()
        for key in cc_keys:
            if key in callb and callb[len(key)] == "%":
                param = callb[len(key)+1:len(callb)]
                handle_goto(chat_id, key, composite_callbacks, simple_buttons, param)
                return
        handle_unknown_input(chat_id)
        print(callb + ": callback undefined")
        return

def execute_script(script, chat_id, sql, sql_result, param):
    eval(script, None, locals())

def set_user_state(chat_id, state):
    db_helper.do_sql(bot_tree["database"]["set_user_state"], [chat_id, state, state])

def get_user_state(chat_id):
    return db_helper.do_sql(bot_tree["database"]["get_user_state"], [chat_id])[0][0]

def parse_state(state:str):
    level_str = state[0:state.find("%")]
    level = int( level_str )
    tmp = state[state.find("%")+1:len(state)]
    funnel = tmp[0:tmp.find("%")]
    tmp = tmp[tmp.find("%")+1:len(tmp)]
    param = tmp
    return level, funnel, param

def play_funnel_level(chat_id, state, message):
    level, funnel, param = parse_state(state)
    level_content = bot_tree["main"]["funnels"]

    for i in range(level):
        if i == 0:
            level_content = level_content[funnel]
        else:
            level_content = level_content["next"]
            if not level_content:
                set_user_state(chat_id, None)
    
    if message.text:
        

    if "next" in level_content.keys():
        level += 1
        state = str(level) + funnel + param
        set_user_state(chat_id, state)

def run():
    if "HEROKU" in list(os.environ.keys()):
        logger = telebot.logger
        logger.setLevel(logging.INFO)
        
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