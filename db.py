import os
import sqlite3

# From: https://goo.gl/YzypOI
def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


class DatabaseDriver(object):
    """
    Database driver for the Task app.
    Handles with reading and writing data with the database.
    """

    def __init__(self):
        self.conn = sqlite3.connect("venmo.db", check_same_thread = False)
        self.create_user_table()
        
    def create_user_table(self):
        """
        Use SQL to create a new table
        """
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          name TEXT NOT NULL,
                          username TEXT NOT NULL,
                          password TEXT NOT NULL,
                          balance INTEGER DEFAULT 0
                          );""")
        
    def delete_user_table(self):
        """
        Use SQL to delete the table if exists
        """
        self.conn.execute("""
        DROP TABLE IF EXISTS users;
                          """)
    
    def get_all_users(self):
        """
        Use SQL to return all users
        """
        cursor = self.conn.execute("SELECT * FROM users")
        users = []
        for row in cursor:
            users.append({"id": row[0], "name": row[1], "username": row[2]})
        return users
    
    def insert_user(self, name, username, password, balance):
        """
        Using SQL, create and place a new user into the users table
        """
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users(name, username, password, balance) VALUES(?, ?, ?, ?);", (name, username, password, balance))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_user_by_id(self, user_id, password):
        """
        Using SQL, get a user by their id and checks to makes sure passwords are the same, but does not return password for security
        """
        cursor = self.conn.execute("SELECT * FROM users WHERE id = ? AND password = ?;", (user_id, password))
        for row in cursor:
            return ({"id": row[0], "name": row[1], "username": row[2], "balance": row[4]})
        return None
    
    def delete_user_by_id(self, user_id):
        """
        Using SQL, delete a user by specified ID
        """
        cursor = self.conn.execute("DELETE FROM users WHERE id = ?;", (user_id,))
        self.conn.commit()
        for row in cursor:
            return ({"id": row[0], "name": row[1], "username": row[2]})
        return None
    
    def send_money(self, sender_id, receiver_id, amount, password):
        """
        Using SQL to send money from one user to another
        """
        self.conn.execute("UPDATE users SET balance = balance - ? WHERE id = ? AND password = ?;", (amount, sender_id, password))
        self.conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?;", (amount, receiver_id))
        self.conn.commit()


# Only <=1 instance of the database driver
# exists within the app at all times
DatabaseDriver = singleton(DatabaseDriver)
