import json

def bot_json_to_obj():
    data = None
    with open("bot.json", "r") as read_file:
        data = json.load(read_file)
    return data