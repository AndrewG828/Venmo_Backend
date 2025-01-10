import os
import sqlite3
from pytz import timezone
from datetime import datetime, timezone as tz
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

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
        self.create_transactions_table()
        self.create_friends_table()
        
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
                          balance INTEGER DEFAULT 0,
                          email TEXT NOT NULL
                          );""")
    
    def create_transactions_table(self):
        """
        Using SQL create a table for transactions
        """
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions(
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          sender_id INTEGER NOT NULL,
                          receiver_id INTEGER NOT NULL,
                          amount INTEGER DEFAULT 0,
                          message TEXT,
                          accepted BOOLEAN,
                          FOREIGN KEY (sender_id) REFERENCES users(id),
                          FOREIGN KEY (receiver_id) REFERENCES users(id)
                          );""")
        
    def create_friends_table(self):
        """
        Using SQL create a table for friends
        """
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS friends(
                          user_id INTEGER NOT NULL,
                          friend_id INTEGER NOT NULL,
                          PRIMARY KEY(user_id, friend_id),
                          FOREIGN KEY(user_id) REFERENCES users(id),
                          FOREIGN KEY(friend_id) REFERENCES users(id)
                          );""")
        
    def delete_user_table(self):
        """
        Use SQL to delete the table if exists
        """
        self.conn.execute("""
        DROP TABLE IF EXISTS users;
                          """)
    
    def delete_transactions_table(self):
        """
        Use SQL to delete the table if exists
        """
        self.conn.execute("DROP TABLE IF EXISTS transactions;")

    def delete_friends_table(self):
        """
        Use SQL to delete the table if exists
        """
        self.conn.execute("DROP TABLE IF EXISTS friends")
    
    def get_all_users(self):
        """
        Use SQL to return all users
        """
        cursor = self.conn.execute("SELECT * FROM users")
        users = []
        for row in cursor:
            users.append({"id": row[0], "name": row[1], "username": row[2], "email": row[5]})
        return users
    
    def get_all_users_testing(self):
        """
        Use SQL to return all Users and their information including password for testing
        """
        cursor = self.conn.execute("SELECT * FROM users")
        users = []
        for row in cursor:
            users.append({"id": row[0], "name": row[1], "username": row[2], "password": row[3], "balance": row[4], "email": row[5]})
        return users
    
    def insert_user(self, name, username, password, balance, email):
        """
        Using SQL, create and place a new user into the users table
        """
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users(name, username, password, balance, email) VALUES(?, ?, ?, ?, ?);", (name, username, password, balance, email))
        self.conn.commit()
        return cursor.lastrowid
    
    def insert_change_email(self, user_id, email):
        """
        Using SQL insert or change the email of a user that is logged in
        """
        self.conn.execute("INSERT INTO users(email) VALUES (?) WHERE id = ?;", (email, user_id))
        self.conn.commit()
    
    def create_friendship(self, user_id, friend_id):
        """
        Using SQL, create a friendship between two ids
        """
        self.conn.execute("INSERT INTO friends(user_id, friend_id) VALUES(?, ?);", (user_id, friend_id))
        self.conn.execute("INSERT INTO friends(user_id, friend_id) VALUES(?, ?);", (friend_id, user_id))
        self.conn.commit()
    
    def get_user_by_id(self, user_id):
        """
        Using SQL, get a user by their id and checks to makes sure passwords are the same, but does not return password for security
        """
        user_transactions = []
        cursor = self.conn.execute("SELECT * FROM transactions WHERE sender_id = ? OR RECEIVER_ID = ?;", (user_id, user_id))
        for row in cursor:
            user_transactions.append({"id": row[0], "timestamp": row[1], "sender_id": row[2], "receiver_id": row[3], "amount": row[4], "message": row[5], "accepted": row[6]})
        cursor = self.conn.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
        for row in cursor:
            return ({"id": row[0], "name": row[1], "username": row[2], "balance": row[4], "email": row[5], "transactions": user_transactions})
        return None
    
    def get_friends(self, user_id):
        """
        Using SQL get the friends of a user entered
        """
        cursor = self.conn.execute("SELECT u.id, u.name, u.username FROM friends f JOIN users u ON f.friend_id = u.id WHERE f.user_id = ?;", (user_id,))
        friends = []
        for row in cursor:
            friends.append({"id": row[0], "name": row[1], "username": row[2]})
        return friends
    
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

    def send_email(self, to_email, subject, content):
        """
        Sends an email using SendGrid.
        """
        message = Mail(
            from_email="cswarg828@gmail.com",
            to_emails=to_email,
            subject=subject,
            html_content=content
        )
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            print(f"Email sent to {to_email}: {response.status_code}")
        except Exception as e:
            print(f"Error sending email: {e}")

    def send_request_money(self, sender_id, receiver_id, amount, message, accepted):
        """
        Using SQL, create a transaction by sending or requesting money
        """
        cursor = self.conn.execute("INSERT INTO transactions(sender_id, receiver_id, amount, message, accepted, timestamp) VALUES (?, ?, ?, ?, ?, ?);", (sender_id, receiver_id, amount, message, accepted, datetime.now())) 
        self.conn.commit()
        if accepted is True:
            sender = self.get_user_by_id(sender_id)
            receiver = self.get_user_by_id(receiver_id)
            self.send_email(
                sender["email"],
                "Transaction Sent",
                f"""
                <p>Hi {sender['name']},</p>
                <p>You sent ${amount} to {receiver['name']} with the message: "{message}".</p>
                <p>Thanks for using our app!</p>
                """
            )
            self.send_email(
                receiver["email"],
                "Transaction Received",
                f"""
                <p>Hi {receiver['name']},</p>
                <p>You received ${amount} from {sender['name']} with the message: "{message}".</p>
                <p>Thanks for using our app!</p>
                """
            )
        return cursor.lastrowid
    
    def get_transaction_by_id(self, transaction_id):
        """
        Using SQL get transaction by id
        """
        cursor = self.conn.execute("SELECT * FROM transactions WHERE id = ?;", (transaction_id,))
        for row in cursor:
            return ({"id": row[0], "timestamp": row[1], "sender_id": row[2], "receiver_id": row[3], "amount": row[4], "message": row[5], "accepted": row[6]})
        return None
    
    def accept_deny_payment_request(self, transaction_id, accepted):
        """
        Using SQL accept or deny a payment if the accepted field is null
        """
        self.conn.execute("UPDATE transactions SET accepted = ? WHERE id = ?;", (accepted, transaction_id))
        self.conn.commit()
        if bool(accepted) is True:
            target_transaction = self.get_transaction_by_id(transaction_id)
            sender = self.get_user_by_id(target_transaction["sender_id"])
            receiver = self.get_user_by_id(target_transaction["receiver_id"])
            amount = target_transaction["amount"]
            message = target_transaction["message"]
            self.send_email(
                sender["email"],
                "Transaction Sent",
                f"""
                <p>Hi {sender['name']},</p>
                <p>You sent ${amount} to {receiver['name']} with the message: "{message}".</p>
                <p>Thanks for using our app!</p>
                """
            )
            self.send_email(
                receiver["email"],
                "Transaction Received",
                f"""
                <p>Hi {receiver['name']},</p>
                <p>You received ${amount} from {sender['name']} with the message: "{message}".</p>
                <p>Thanks for using our app!</p>
                """
            )
    
    """
    def get_transaction_by_id(self, transaction_id):
        
        Using SQL get transaction by id
        
        cursor = self.conn.execute("SELECT * FROM transactions WHERE id = ?;", (transaction_id,))
        for row in cursor:
            utc_timestamp = datetime.now(tz.utc)
            user_time_zone = "America/New_York"  # Replace this with detected time zone
            local_time = datetime.fromisoformat(utc_timestamp.astimezone(timezone(user_time_zone)))
            return ({
                "id": row[0],
                "timestamp": local_time,
                "sender_id": row[2],
                "receiver_id": row[3],
                "amount": row[4],
                "message": row[5],
                "accepted": row[6]
            })
        return None
    """

    def get_all_transactions(self):
        """
        Using SQL get all transactions
        """
        cursor = self.conn.execute("SELECT * FROM transactions")
        transactions = []
        for row in cursor:
            transactions.append({"id": row[0], "timestamp": row[1], "sender_id": row[2], "receiver_id": row[3], "amount": row[4], "message": row[5], "accepted": row[6]})
        return transactions
    
    def get_transaction_by_user_id(self, user_id):
        """
        Using SQL get all transaction that a user is invovled in
        """
        cursor = self.conn.execute("""SELECT s.name AS sender_name, r.name AS receiver_name, t.amount, t.message, t.accepted, t.timestamp FROM transactions t JOIN users s ON t.sender_id = s.id
                                   JOIN users r ON t.receiver_id = r.id WHERE t.sender_id=? OR t.receiver_id=?;""", (user_id, user_id))
        transactions = []
        for row in cursor:
            transactions.append({
                "sender_name": row[0],
                "receiver_name": row[1],
                "amount": row[2],
                "message": row[3],
                "accepted": bool(row[4]),
                "timestamp": row[5]
            })
        return transactions

    



# Only <=1 instance of the database driver
# exists within the app at all times
DatabaseDriver = singleton(DatabaseDriver)
