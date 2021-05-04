from psycopg2 import connect
from typing import Dict
import json_helper

bot_tree:Dict = json_helper.bot_json_to_obj()
conn_params = bot_tree["params"]["db"]

def create_table(conn_params):#, table_name, table_fields):
    """ self.data_cursor.execute("CREATE TABLE IF NOT EXISTS item (name varchar(45) NOT NULL"""
    with connect(host=conn_params["host"],\
        database=conn_params["database"],\
        user=conn_params["user"],\
        port=conn_params["port"],\
        password=conn_params["password"])\
    as conn: 
        print("Connected to DB")
        with conn.cursor() as cursor:
           print("DB: cursor created")

create_table(conn_params)