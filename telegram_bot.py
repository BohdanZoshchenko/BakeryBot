from os import stat
from modules import *
import telegram_bot_tree_funcs as bot_helper
from inspect import signature

bot = bot_helper.bot
bot_tree = bot_helper.bot_tree

def handle_goto(chat_id, goto:str, gotos:Dict, simple_buttons = None, param = None, message = None):
    if goto == None:
        #print("Goto is None")
        return

    text = None
    if "text" in gotos[goto].keys():
        text = gotos[goto]["text"]
    else:
        #print(goto + ": Goto has no text message")
        pass

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
        state = get_user_state(chat_id)
        script = "bot_helper." + func + str(signature(eval("bot_helper." + func)))
        execute_script(script, chat_id, sql, sql_result, param, state)
                
        return
    # Block end

    # If there was a script, this message will not be sent 
    if text:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

def handle_funnel(chat_id, call_info=None, msg_text=None, param = None):
    key = None
    if call_info!=None:
        key = call_info
    elif msg_text!=None:
        key = msg_text

    state = get_user_state(chat_id)
    
    if not state:
        if not key:
            return
        state = []
        state.append("0")
        state.append(key)
    if param:
        if len(state) < 3:
            state.append([param])
        else:
            state[2].append(param)
    
    set_user_state(chat_id, state)
    play_funnel_level(chat_id, state, msg_text, call_info)

def handle_unknown_input(chat_id):
    handle_goto(chat_id, "unknown_input", gotos=bot_tree["main"])

@bot.message_handler()
def handle_user_messages_and_simple_buttons(message:types.Message):
    chat_id = message.chat.id

#############REMOVE
    #set_user_state(chat_id, None)

    gotos:Dict = bot_tree["main"]["simple_gotos"]
    commands:Dict = bot_tree["main"]["commands"]
    simple_buttons = bot_tree["main"]["simple_buttons"]
    funnels = bot_tree["main"]["funnels"]

    state = get_user_state(chat_id)


    if message.text != None and message.text != "":
        # funnel
        if state:
            for k in funnels.keys():
                handle_funnel(chat_id, msg_text=message.text)
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
                            m = message
                            handle_goto(chat_id, goto, gotos, simple_buttons, message = m)
                        else:
                            handle_unknown_input(chat_id)
                            #print(goto + ":Goto undefined")
                    else:
                        handle_unknown_input(chat_id)
                        #print(command + "Command has no goto")
                else:
                    handle_unknown_input(chat_id)
                    #print(command + ":Command undefined")
            else:
                handle_unknown_input(chat_id)
                #print("No command body")
        else:
            # simple buttons and messages
            goto = None
            for row in simple_buttons:
                for button in row:
                    if button[1] == message.text and button[1] in gotos.keys():
                        goto = button[1]
                        m = message
                        handle_goto(chat_id, goto, gotos, simple_buttons, message = m)
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

    state = get_user_state(chat_id)
    
    if state and state[0]:
        on_user_distracted(chat_id)
        return

    if callb != "":
        # funnel
        if funnels:
            if not state:
                f_keys = funnels.keys()
                for key in f_keys:
                    if key in callb and callb[len(key)] == "%" and callb.count('%') == 1:
                        p = callb[len(key)+1:len(callb)]
                        handle_funnel(chat_id, call_info=key, param=p)
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

def execute_script(script, chat_id, sql, sql_result, param, state):
    eval(script, None, locals())

def set_user_state(chat_id, state):
    if state == None:
        state = [None, None, None]
    level = state[0]
    funnel = state[1]
    params = state[2]
    db_helper.do_sql(bot_tree["database"]["set_user_state"], [chat_id, level, funnel, params, level, funnel, params])

def get_user_state(chat_id):
    sql_result = db_helper.do_sql(bot_tree["database"]["get_user_state"], [chat_id])
    if len(sql_result) == 0:
        return None
    return sql_result[0][0], sql_result[0][1], sql_result[0][2]

def play_funnel_level(chat_id, state, msg_text=None, call_data=None):
    if not state:
        return
    level, funnel, params = state
    if level:
        level = int(level)
        level_content = get_funnel_level_content(chat_id, state)
        if msg_text:
            print(state)
            type = None
            if "input_type" in level_content.keys(): 
                type = level_content["input_type"]
            min = None
            if "min" in level_content.keys():
                min = level_content["min"]
            max = None
            if "max" in level_content.keys():
                max = level_content["max"]
            if type != None:
                valid_info = is_value_valid(msg_text, level_content["input_type"], min, max)
                #print(valid_info)

        if "text" in level_content:
            bot.send_message(chat_id, level_content["text"], parse_mode="Markdown")

        if "func" in level_content:
            s = state
            print(s)
            execute_script(level_content["func"], chat_id, sql=None, sql_result=None, param=None, state=s)

        if str(level+1) in level_content.keys():   
            level += 1
            state = [str(level), funnel, params]

    set_user_state(chat_id, state)

def get_funnel_level_content(chat_id, state):
    level, funnel, params = state
    level = int(level)
    level_content = bot_tree["main"]["funnels"]
    #print(level)
    for i in range(0, int(level)+1):
        if i == 0:
            level_content = level_content[funnel]
        else:
            if str(level+1) in level_content:
                level_content = level_content[str(level+1)]
            else:
                level_content = None
                set_user_state(chat_id, None)
    return level_content

def is_value_valid(value, type:str, min=None, max=None):
    x = None
    try:
        exec("x="+type+"("+value+")", locals())
    except:
        return "type_mismatch"
    if isinstance(x, str):
        if min != None and len(x) < min:
            return "too_little"
        if max != None and len(x) > max:
            return "too_big"
    else:
        if min != None and x < min:
            return "too_little"
        if max != None and x > max:
            return "too_big"
    return "ok"

def on_user_distracted(chat_id): 
    text = bot_tree["main"]["on_user_distracted"]
    state = get_user_state(chat_id)
    if not state:
        return False
    l, funnel, p = state
    bot.send_message(chat_id, text, parse_mode="Markdown")
    handle_funnel(chat_id, msg_text = funnel, call_info=funnel)
    return True

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