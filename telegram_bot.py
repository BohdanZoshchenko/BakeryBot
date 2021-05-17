from inspect import isawaitable
from modules import *
import telegram_bot_tree_funcs as bot_helper
from telegram_bot_tree_funcs import get_user_state, set_user_state
from settings import *

#### most of defs make without async/await (except callback and message handler)

nest_asyncio.apply()

bot = bot_helper.bot
bot_tree = bot_helper.bot_tree


simple_callbacks: Dict = bot_tree["user"]["simple_callbacks"]
composite_callbacks: Dict = bot_tree["user"]["composite_callbacks"]
simple_buttons = bot_tree["user"]["simple_buttons"]
funnels = bot_tree["user"]["funnels"]

async def handle_goto(chat_id, goto: str, gotos: Dict, simple_buttons=None, param=None, message=None):
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
        await handle_goto(chat_id, gotos[goto]["goto"], gotos, simple_buttons, param)

    # This block should be always in the end, before sending message
    if "func" in gotos[goto].keys():
        func = gotos[goto]["func"]
        state = get_user_state(chat_id)
        await execute_script(func, chat_id, sql, sql_result, param, state)

        return
    # Block end

    # If there was a script, this message will not be sent
    if text:
        await bot.send_message(chat_id, text, reply_markup=markup, parse_mode="html")


async def start_funnel(chat_id, call_info=None, msg=None, param=None):
    state = "0", call_info, param
    set_user_state(chat_id, state)
    await play_funnel_level(chat_id, state, msg)

async def handle_unknown_input(chat_id):
    await handle_goto(chat_id, "unknown_input", gotos=bot_tree["user"])

@dp.message_handler(content_types=ContentType.ANY)
async def handle_user_messages_and_simple_buttons(message: types.Message):
    chat_id = message.chat.id

    await add_admin_button(chat_id)

    gotos: Dict = bot_tree["user"]["simple_gotos"]
    commands: Dict = bot_tree["user"]["commands"]
    simple_buttons = bot_tree["user"]["simple_buttons"]
    funnels = bot_tree["user"]["funnels"]

    # funnel
    state = get_user_state(chat_id)

    if state is not None and state != [None, None, None] and state[0] != "0" and state[2] is not None:
        print(state)
        await play_funnel_level(chat_id, state, message)
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
                            await handle_goto(chat_id, goto, gotos,
                                        simple_buttons, message=m)
                        else:
                            await handle_unknown_input(chat_id)
                            #(goto + ":Goto undefined")
                    else:
                        await handle_unknown_input(chat_id)
                        #(command + "Command has no goto")
                else:
                    await handle_unknown_input(chat_id)
                    #(command + ":Command undefined")
            else:
                await handle_unknown_input(chat_id)
                #("No command body")
        else:
            # simple buttons and messages
            goto = None
            for row in simple_buttons:
                for button in row:
                    if button[1] == message.text and button[1] in gotos.keys():
                        goto = button[1]
                        m = message
                        await handle_goto(chat_id, goto, gotos,
                            simple_buttons, message=m)
                        return
            await handle_unknown_input(chat_id)
    else:
        await handle_unknown_input(chat_id)

@dp.callback_query_handler(lambda callback_query:True)
async def handle_inline_buttons_callbacks(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id

    await add_admin_button(chat_id)

    callb = callback.data
    print("Callback:"+callback.data)
    if callb != "":
        # funnel entry
        f_keys = funnels.keys()
        for key in f_keys:
            print("key:"+key)
            if (key+"%") in callb:
                p = callb[len(key)+1:len(callb)]
                await start_funnel(chat_id, call_info=key, param=[p])
                return
            elif key==callb:
                await start_funnel(chat_id, call_info=key, param=[])
                return
            else:
                set_user_state(chat_id, None)

        if callb in simple_callbacks.keys():
            await handle_goto(chat_id, callb, simple_callbacks, simple_buttons)
            return
        else:
            cc_keys = composite_callbacks.keys()
            for key in cc_keys:
                if key in callb and callb[len(key)] == "%":
                    param = [callb[len(key)+1:len(callb)]]
                    await handle_goto(chat_id, key, composite_callbacks,
                        simple_buttons, param)
                    return

async def execute_script(func_name, chat_id=None, sql=None, sql_result=None, param=None, state=None):
    func_name = "bot_helper." + func_name
    func = eval(func_name)
    script = func_name + \
            str(signature(func))
    if iscoroutinefunction(func) or isawaitable(func):
        await eval(script, globals(), locals())
    else:
        eval(script, globals(), locals())

async def play_funnel_level(chat_id, state, msg=None):
    if state is None or state == [None, None, None]:
        return False
    
    level_content = get_funnel_level_content(chat_id, state)
    if level_content is None:
        return False

    level, funnel, params = state
    if msg is None and level is not None:
        level = int(level)
        if level == 0:
            await funnel_execute(chat_id, level, funnel, params, x=None)
            return True
        else:
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

        if msg_content is not None:
            valid_info = is_value_valid(msg, level_content)
            if valid_info[0] != "ok":
                await on_wrong_input(chat_id, valid_info[0], level_content)
                await funnel_execute(chat_id, level - 1, funnel, params, x=None)
                return False
            else:
                x = valid_info[1]
                x = str(x)
                if len(state) < 3 or state[2] is None or state[2] == []:
                    state.append([x])
                else:
                    state[2].append(x)
        else:
            return False
        await funnel_execute(chat_id, level, funnel, params, x)

        return True
    else:
        return False

async def funnel_execute(chat_id, level, funnel, params, x=None):
    state = [level, funnel, params]
    level_content = get_funnel_level_content(chat_id, state)
    if level_content is None:
        return False
    if "text" in level_content.keys():
        await bot.send_message(chat_id, level_content["text"], parse_mode="html")
    if "func" in level_content.keys():
        s = state
        func = level_content["func"]
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
        await execute_script(func, chat_id, sql,
            sql_result=None, param=p, state=s)

    level = int(level)
    level += 1
    level = str(level)
    state = to_state(level, funnel, params)
    if get_funnel_level_content(chat_id, state) is None:
        print("yes")
        state = [None, None, None]

    set_user_state(chat_id, state)

def is_value_valid(msg, level_content):

    def str_to_number(value:str, input_type:str, min = None, max = None, after_comma = None):

        def correct_number(value, min = None, max = None, after_comma = None):
            if not isinstance(value, float) and not isinstance(value, int):
                return "type_mismatch", value
            if isinstance(value, float):
                value = round(value, after_comma)
            if min is not None and value < min:
                return "too_little", value
            if max is not None and value > max:
                return "too_big", value
            return "ok", value

        if input_type == "int":
            try:
                return correct_number(int(value), min, max, after_comma)
            except:
                return "type_mismatch", value
        elif input_type == "float":
            try:
                value = value.replace(",", ".")
                return correct_number(float(value), min, max, after_comma)
            except:
                return "type_mismatch", value

    value = None
    value_type = None

    if isinstance(msg, types.Message):
        value = eval("msg." + msg.content_type)
        value_type = msg.content_type
        if value_type == "text":
            value_type = "str"
    else:
        value = msg
        value_type = str(type(value))
    
    input_type = None
    if "input_type" in level_content.keys():
        input_type = level_content["input_type"]
        if input_type == "text":
            input_type = "str"
        elif input_type == "image":
            input_type = "photo"
        if input_type == value_type:
            return "ok", value
        elif (input_type == "float" or input_type == "int") and value_type == "str":
            min = None
            if "min" in level_content.keys():
                min = level_content["min"]
            max = None
            if "max" in level_content.keys():
                max = level_content["max"]
            after_comma = None
            if "after_comma" in level_content.keys():
                after_comma = level_content["after_comma"]
            return str_to_number(value, input_type, min, max, after_comma)
        else:
            return "type_mismatch", value
    else:
        return "type_mismatch", value

def error_exists(error: str, level_content):
    for error in level_content["errors"].keys():
        return True

    return False

async def on_wrong_input(chat_id, error: str, level_content):
    text = bot_tree["user"]["funnel_unknown_input"]
    x = "errors" in level_content.keys()

    if x and error_exists(error, level_content):
        text = level_content["errors"][error]
    await bot.send_message(chat_id, text, parse_mode="html")


def to_state(level, funnel, params):
    return [str(level), funnel, params]

def get_funnel_level_content(chat_id, state):
    if state is None or state == [None, None, None]:
        set_user_state(chat_id, [None, None, None])
        return None
    level, funnel, params = state
    if funnel is None or funnel == "None":
        set_user_state(chat_id, [None, None, None])
        return None
    level = str(level)
    if level is None:
        level_content = None
        set_user_state(chat_id, None)
    else:
        state = to_state(level, funnel, params)
        level_content = bot_tree["user"]["funnels"]

        if level in level_content[funnel].keys():
            level_content = level_content[funnel][level]
            set_user_state(chat_id, state)
        else:
            level_content = None
            set_user_state(chat_id, None)
    return level_content

async def add_admin_button(chat_id):
    admin_id_list = db_helper.do_sql(bot_tree["database"]["get_admins"], [])
    if len(admin_id_list)>0:
        for i in admin_id_list:
            if i[0] == chat_id:
                if db_helper.do_sql(bot_tree["database"]["get_keyboard_created"], [chat_id])[0][0]:
                    return
                if db_helper.do_sql(bot_tree["database"]["get_admin_on"], [chat_id])[0][0]:
                    return
                admin_keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True)
                button = types.KeyboardButton("Адмін-панель")
                admin_keyboard.add(button)
                await bot.send_message(chat_id, text = "Ви - адміністратор. Щоб відкрити адмін-панель, натисніть кнопку Адмін-панель на клавіатурі", reply_markup=admin_keyboard)
                db_helper.do_sql(bot_tree["database"]["set_keyboard_created"], [True, chat_id])
                return True
    return False

@dp.message_handler()
async def admin_mode_on(message : types.Message):
    if message.text != "Адмін-панель":
        return
    admin_id_list = db_helper.do_sql(bot_tree["database"]["get_admins"], [])
    if len(admin_id_list)>0:
        for i in admin_id_list:
            if i[0] == message.chat.id:
                db_helper.do_sql(bot_tree["database"]["set_admin_on"], [True, message.chat.id])
                #if db_helper.do_sql(bot_tree["database"]["get_admin_on"], [message.chat.id])[0][0]:
                #    return
                set_user_state(message.chat.id, [None, None, None])
                handle_goto(message.chat.id, "start", gotos=bot_tree["admin"])
                
                
        
@dp.callback_query_handler(lambda callback_query:True)
async def quit_admin(callback):
    if callback.data == "quit_admin":
        db_helper.do_sql(bot_tree["database"]["set_admin_on"], [False, callback.message.chat.id])

async def on_startup(dp):
    logging.warning(
    'Starting connection. ')
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)

async def on_shutdown(dp):
    logging.warning('Bye! Shutting down webhook connection')


async def main():
    if "HEROKU" in list(os.environ.keys()):
        # webserver settings
        WEBAPP_HOST = '0.0.0.0'
        WEBAPP_PORT = int(os.getenv('PORT'))

        logging.basicConfig(level=logging.INFO)
        
        start_webhook(dispatcher=dp, 
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT)
    else:
        await bot.delete_webhook()
        executor.start_polling(dp, skip_updates = True)


asyncio.run(main())
