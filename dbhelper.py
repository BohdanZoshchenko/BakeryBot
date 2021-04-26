from psycopg2 import connect, extensions, sql
import orders_control

class DBHelper:
    data_cursor = None
    connection = None

    def __init__(self):
        self.connection = connect(dbname = "python_test", user = "objectrocket", host = "localhost",password = "mypass")

        self.data_cursor = self.connection.cursor()

        #self.data_cursor.execute("DROP TABLE category")
        #self.data_cursor.execute("DROP TABLE item")
        #self.data_cursor.execute("DROP TABLE client_order")
        
        
        
        #self.data_cursor.execute("UPDATE item SET name = 'Торт Наполеон' WHERE name = 'Наполеон';")
        #self.data_cursor.execute("UPDATE item SET name = 'Торт Ванільно-ягідний' WHERE name = 'Ванільно-ягідний';")
        #self.data_cursor.execute("UPDATE item SET name = 'Торт Прага' WHERE name = 'Прага';")
        
        
        
        self.data_cursor.execute("CREATE TABLE IF NOT EXISTS category (price integer NOT NULL DEFAULT '450', PRIMARY KEY (price))")
        
        self.data_cursor.execute("CREATE TABLE IF NOT EXISTS item (name varchar(45) NOT NULL, description varchar(450) NOT NULL, photo bytea NOT NULL, price integer NOT NULL DEFAULT '450')")
        

        self.data_cursor.execute("CREATE TABLE IF NOT EXISTS client_order (client_id integer NOT NULL DEFAULT '450', description varchar NOT NULL, photo bytea)")

        self.connection.commit()

    def add_order(self, client_id):
        sql = """INSERT INTO client_order VALUES(%s,%s,%s);"""

        print(orders_control.orders[client_id][0])
        self.data_cursor.execute(sql, [client_id, orders_control.orders[client_id][0], orders_control.orders[client_id][1]])
        print("order added")
        self.connection.commit()

    def save_category_to_db(self, category):
        price = category.price
        sql = """INSERT INTO category VALUES(%s);"""
        
        self.data_cursor.execute(sql, [price])
        self.connection.commit()

        #self.data_cursor.close()
        #self.connection.close()
        print('success')

    def update_category_in_db(self, price):
        pass

    def save_item_to_db(self, item):
        sql = """INSERT INTO item VALUES(%s,%s,%s,%s);"""
        
        self.data_cursor.execute(sql, [item.name, item.description, item.photo, item.price])
        self.connection.commit()

        print('Item added to DB)))!')

    def delete_category_from_db(self, price):
        sql = """DELETE FROM category WHERE price = %s;"""
        
        self.data_cursor.execute(sql, [price])
        self.connection.commit()

    def get_each_category_from_db(self):
        sql = """SELECT * FROM category ORDER BY price"""
        self.data_cursor.execute(sql, [])
        rows = []
        for row in self.data_cursor:
            rows.append(row)
        self.connection.commit()
        return rows

    def get_each_item_from_db(self):
        sql = """SELECT * FROM item ORDER BY price"""
        self.data_cursor.execute(sql, [])
        rows = []
        for row in self.data_cursor:
            rows.append(row)
        self.connection.commit()
        return rows

    def get_items_by_price_from_db(self, price):
        sql = """SELECT * FROM item WHERE price = %s"""
        self.data_cursor.execute(sql, [price])
        rows = []
        for row in self.data_cursor:
            rows.append(row)
        self.connection.commit()
        return rows

    def get_category_by_price_from_db(self, price):
        sql = """SELECT * FROM category WHERE price = %s"""
        self.data_cursor.execute(sql, [price])
        rows = []
        for row in self.data_cursor:
            rows.append(row)
        self.connection.commit()
        return rows[0]

    def get_item_by_name_from_db(self, name):
        sql = """SELECT * FROM item WHERE name = %s"""
        self.data_cursor.execute(sql, [name])
        rows = []
        for row in self.data_cursor:
            rows.append(row)
        self.connection.commit()
        return rows[0]


    def get_item_from_db(self, price, name):
        sql = """SELECT * FROM item WHERE price = %s AND name = %s"""
        self.data_cursor.execute(sql, [price, name])
        rows = []
        for row in self.data_cursor:
            rows.append(row)
        self.connection.commit()
        return rows

##from contextlib import closing

##with closing(psycopg2.connect(...)) as conn:
  ##  with conn.cursor() as cursor:
     ##   cursor.execute('SELECT * FROM airport LIMIT 5')