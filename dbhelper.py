from psycopg2 import connect, extensions, sql
class DBHelper:
    data_cursor = None
    connection = None

    def __init__(self):
        self.connection = connect(dbname = "python_test", user = "objectrocket", host = "localhost",password = "mypass")

        self.data_cursor = self.connection.cursor()

        self.data_cursor.execute("CREATE TABLE IF NOT EXISTS category (price integer NOT NULL DEFAULT '450', PRIMARY KEY (price))")
        
        self.data_cursor.execute("CREATE TABLE IF NOT EXISTS item (name varchar(45) NOT NULL, description varchar(450) NOT NULL, photo bytea NOT NULL, price integer NOT NULL DEFAULT '450')")
        
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
        sql = """SELECT * FROM category"""
        self.data_cursor.execute(sql, [])
        rows = []
        for row in self.data_cursor:
            rows.append(row)
        self.connection.commit()
        return rows

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