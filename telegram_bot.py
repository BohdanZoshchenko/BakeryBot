from os import stat
from modules import *
import telegram_bot_tree_funcs as bot_helper
from inspect import signature

bot = bot_helper.bot
bot_tree = bot_helper.bot_tree

simple_callbacks: Dict = bot_tree["main"]["simple_callbacks"]
composite_callbacks: Dict = bot_tree["main"]["composite_callbacks"]
simple_buttons = bot_tree["main"]["simple_buttons"]
funnels = bot_tree["main"]["funnels"]


def handle_goto(chat_id, goto: str, gotos: Dict, simple_buttons=None, param=None, message=None):
    if goto == None:
        #("Goto is None")
        return

    text = None
    if "text" in gotos[goto].keys():
        text = gotos[goto]["text"]
    else:
        #(goto + ": Goto has no text message")
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
                    buttons_row.append(types.InlineKeyboardButton(
                        text=button[0], callback_data=button[1]))
                inline_keyboard.row(*buttons_row)
            markup = inline_keyboard

        simple_keyboard = None
        if not inline_keyboard and simple_buttons and "simple_buttons" in gotos[goto].keys():
            simple_keyboard = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True)
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

        sql_result = db_helper.do_sql(sql, param)

    if "goto" in gotos[goto].keys():
        handle_goto(chat_id, gotos[goto]["goto"], gotos, simple_buttons, param)

    # This block should be always in the end, before sending message
    if "func" in gotos[goto].keys():
        func = gotos[goto]["func"]
        state = get_user_state(chat_id)
        script = "bot_helper." + func + \
            str(signature(eval("bot_helper." + func)))
        execute_script(script, chat_id, sql, sql_result, param, state)

        return
    # Block end

    # If there was a script, this message will not be sent
    if text:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="html")


def start_funnel(chat_id, call_info=None, msg=None, param=None):
    state = "0", call_info, param
    set_user_state(chat_id, state)
    play_funnel_level(chat_id, state, msg)


def handle_unknown_input(chat_id):
    handle_goto(chat_id, "unknown_input", gotos=bot_tree["main"])


@bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document', 'text', 'location', 'contact', 'sticker'])
def handle_user_messages_and_simple_buttons(message: types.Message):
    chat_id = message.chat.id

    gotos: Dict = bot_tree["main"]["simple_gotos"]
    commands: Dict = bot_tree["main"]["commands"]
    simple_buttons = bot_tree["main"]["simple_buttons"]
    funnels = bot_tree["main"]["funnels"]

    # funnel
    state = get_user_state(chat_id)

    if state is not None and state != [None, None, None]:
        param = message
        if not play_funnel_level(chat_id, get_user_state(chat_id), param):
            state = get_user_state(chat_id)
            level, funnel, params = state
            
            if len(params)-1 >= 0:
                param = params[len(params)-1]
            else:
                param = None
            set_user_state(chat_id,state)
            play_funnel_level(chat_id, get_user_state(chat_id), param)
        return

    if message.text is not None and message.text != "":
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
                            handle_goto(chat_id, goto, gotos,
                                        simple_buttons, message=m)
                        else:
                            handle_unknown_input(chat_id)
                            #(goto + ":Goto undefined")
                    else:
                        handle_unknown_input(chat_id)
                        #(command + "Command has no goto")
                else:
                    handle_unknown_input(chat_id)
                    #(command + ":Command undefined")
            else:
                handle_unknown_input(chat_id)
                #("No command body")
        else:
            # simple buttons and messages
            goto = None
            for row in simple_buttons:
                for button in row:
                    if button[1] == message.text and button[1] in gotos.keys():
                        goto = button[1]
                        m = message
                        handle_goto(chat_id, goto, gotos,
                            simple_buttons, message=m)
                        return
            handle_unknown_input(chat_id)
    else:
        handle_unknown_input(chat_id)


@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons_callbacks(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id

    callb = callback.data

    if callb != "":
        # funnel entry
        f_keys = funnels.keys()
        for key in f_keys:
            if key in callb and callb[len(key)] == "%":
                p = callb[len(key)+1:len(callb)]
                start_funnel(chat_id, call_info=key, param=[p])
                return
            else:
                set_user_state(chat_id, None)

        if callb in simple_callbacks.keys():
            handle_goto(chat_id, callb, simple_callbacks, simple_buttons)
            return
        else:
            cc_keys = composite_callbacks.keys()
            for key in cc_keys:
                if key in callb and callb[len(key)] == "%":
                    param = [callb[len(key)+1:len(callb)]]
                    handle_goto(chat_id, key, composite_callbacks,
                        simple_buttons, param)
                    return


def execute_script(script, chat_id, sql, sql_result, param, state):
    eval(script, None, locals())


def set_user_state(chat_id, state):
    if state == None:
        state = [None, None, None]
    level = state[0]
    funnel = state[1]
    params = state[2]
    print(state)
    db_helper.do_sql(bot_tree["database"]["set_user_state"], [
                     chat_id, level, funnel, params, level, funnel, params])


def get_user_state(chat_id):
    sql_result = db_helper.do_sql(
        bot_tree["database"]["get_user_state"], [chat_id])
    if len(sql_result) == 0:
        return None
    state = [sql_result[0][0], sql_result[0][1], sql_result[0][2]]
    print(state)
    return state


def play_funnel_level(chat_id, state, msg=None):
    if state is None or state == [None, None, None]:
        return False
    
    level_content = get_funnel_level_content(chat_id, state)

    level, funnel, params = state
    if msg is None and level is not None:
        level = int(level)
        if level == 0:
            funnel_execute(chat_id, level, level_content, funnel, state, params, x=None)
            return True
        else:
            print("ERROR")
            return False

    msg_content = None
    if msg is not None:
        if msg is types.Message:
            msg_content = eval("msg."+msg.content_type, globals(), locals())
        else:
            msg_content = msg
    x = None
    if level is not None and (int(level) == 0 or msg_content is not None):
        level = int(level)
        if level_content is None:
            return False

        if msg_content is not None:
            valid_info = bot_helper.is_value_valid(msg, level_content)
            if valid_info[0] != "ok":
                print("Not ok")
                on_wrong_input(chat_id, valid_info[0], level_content)
                state[0] = str(int(state[0])-1)
                set_user_state(chat_id, state)
                return False
            else:
                x = valid_info[1]
                if x is float and "after_comma" in level_content.keys():
                    x = round(x, level_content["after_comma"])
                    x = str(x)
                if msg.content_type == "text":
                    x = str(x)
                if len(state) < 3 or state[2] is None or state[2] == []:
                    state.append([x])
                else:
                    state[2].append(x)
        else:
            return False

        funnel_execute(chat_id, level, level_content, funnel, state, params, x)

        return True
    else:
        return False

def funnel_execute(chat_id, level, level_content, funnel, state, params, x=None):
    if "text" in level_content.keys():
        bot.send_message(chat_id, level_content["text"], parse_mode="html")

    if "func" in level_content.keys():
        s = state
        func = level_content["func"]
        script = "bot_helper." + func + \
            str(signature(eval("bot_helper." + func)))
        sql = None
        if "sql" in level_content.keys():
            sql = level_content["sql"]
        if x is not None:
            p = x
        else:
            if params == [] or params is None:
                p = None
            else:
                p = params[len(params)-1]
        execute_script(script, chat_id, sql,
            sql_result=None, param=p, state=s)

    level = int(level)
    level += 1
    level = str(level)
    state = to_state(level, funnel, params)

    if get_funnel_level_content(chat_id, state) is None:
        state = None

    set_user_state(chat_id, state)

def error_exists(error: str, level_content):
    for error in level_content["errors"].keys():
        return True

    return False


def on_wrong_input(chat_id, error: str, level_content):
    text = bot_tree["main"]["funnel_unknown_input"]
    x = "errors" in level_content.keys()

    if x and error_exists(error, level_content):
        text = level_content["errors"][error]
    bot.send_message(chat_id, text, parse_mode="html")


def to_state(level, funnel, params):
    return [str(level), funnel, params]


def get_funnel_level_content(chat_id, state):
    if state is None:
        return None
    level, funnel, params = state
    level = int(level)
    level_content = bot_tree["main"]["funnels"]
    if str(level) in level_content[funnel].keys():
        level_content = level_content[funnel][str(level)]
        set_user_state(chat_id, state)
    else:
        level_content = None
        set_user_state(chat_id, None)

    return level_content


def on_user_distracted(chat_id):
    text = bot_tree["main"]["on_user_distracted"]
    state = get_user_state(chat_id)
    if not state:
        return False
    bot.send_message(chat_id, text, parse_mode="html")
    play_funnel_level(chat_id, state)
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
            bot.set_webhook(
                url=bot_tree["params"]["url"]+bot_tree["params"]["telegram_token"])
            return "?", 200
        from waitress import serve
        serve(server, host="0.0.0.0", port=os.environ.get(
            'PORT', bot_tree["params"]["server_port"]))

    else:
        bot.remove_webhook()
        bot.polling(none_stop=True)


run()
