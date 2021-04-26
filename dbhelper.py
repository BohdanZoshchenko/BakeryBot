import os
import psycopg2

from psycopg2 import connect, extensions, sql
class DBHelper:
    data_cursor = None
    connection = None

    def __init__(self):
        #DATABASE_URL = os.environ['https://bakerybotmariko.herokuapp.com/db']

        self.connection = psycopg2.connect(host="bakerybotmariko.herokuapp.com",database="d9a5qf332rvd60",user="svcsvcnqpcihzf",port=5432,password="d24a90027d702d66f15d5b4eb658eecb672b202d0af5934f82b3aa933373371a")


        self.data_cursor = self.connection.cursor()

        self.data_cursor.execute("CREATE TABLE IF NOT EXISTS category (price integer NOT NULL DEFAULT '450', PRIMARY KEY (price))")

        self.data_cursor.execute("CREATE TABLE IF NOT EXISTS item (name varchar(45) NOT NULL, description varchar(450) NOT NULL, photo bytea, price integer NOT NULL DEFAULT '450', PRIMARY KEY (name))")
        
        self.connection.commit()
        #self.data_cursor.close()
        #self.connection.close()

    def save_category_to_db(self, category):
        price = category.price
        sql = """INSERT INTO category VALUES(%s);"""
        
        self.data_cursor.execute(sql, [price])
        self.connection.commit()

        #self.data_cursor.close()
        #self.connection.close()
        print('success')

    def delete_each_category_from_db(self, price):
        sql = """DELETE FROM category WHERE price = %s;"""
        
        self.data_cursor.execute(sql, [price])
        self.connection.commit()

    def get_each_category_from_db(self):
        sql = """SELECT * FROM category"""
        self.data_cursor.execute(sql, [])
        rows = []
        for row in self.data_cursor:
            rows.append(row)
        self.connection.commit()
        return rows

##from contextlib import closing

##with closing(psycopg2.connect(...)) as conn:
  ##  with conn.cursor() as cursor:
     ##   cursor.execute('SELECT * FROM airport LIMIT 5')
