from psycopg2 import connect
import json_helper
import os

bot_tree = None
conn_params = None

def do_sql(sql:str, fields=None, records_count_to_fetch:int=None):
    result = None
    conn = None
    if "HEROKU" in list(os.environ.keys()):
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = connect(DATABASE_URL, sslmode='require')
    else:
        conn = connect(host=conn_params["host"],\
            database=conn_params["database"],\
            user=conn_params["user"],\
            port=conn_params["port"],\
            password=conn_params["password"])
        #print("Connected to DB")
    with conn.cursor() as cursor:
            #print("DB: cursor created")
        if fields != None:
            cursor.execute(sql, fields)
        else:
            cursor.execute(sql)
            #print("DB: query execution was succesful")
            #print(sql)
        try:
            if not records_count_to_fetch:
                result = cursor.fetchall()
            elif records_count_to_fetch > 0:
                result = cursor.fetchmany(records_count_to_fetch)
                #else:
                   #print("DB: records count variable should be more than zero")
        except:
            pass
    conn.commit()

        #print("DB: commit was succesful")
        #if isinstance(result, list):
        #   print("DB: query result: " + str(result))
    cursor.close()

    return result

def create_tables():
    create_tables = bot_tree["database"]["create_tables"]
    for sql in create_tables:
        do_sql(sql)

bot_tree = json_helper.bot_json_to_obj()
if "HEROKU" in list(os.environ.keys()):
    conn_params = bot_tree["params"]["database"]["production"]
    print("Production DB selected. Be careful with data changing!")
else:
    conn_params = bot_tree["params"]["database"]["development"]
    print("Development DB selected.")

create_tables()
