import json
from flask import Flask, request, jsonify
import db
import hashlib
import os
from dotenv import load_dotenv


DB = db.DatabaseDriver()

load_dotenv()

app = Flask(__name__)

SALT = os.getenv("PASSWORD_SALT").encode('utf-8')
ITERATIONS = int(os.getenv("NUMBER_OF_ITERATIONS"))

def hash_password(password):
    """
    Uses password salting and iterative hashing to hash a passed password
    """
    hashed_password = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        SALT,
        ITERATIONS 
    )
    return hashed_password.hex()

def verify_password(stored_password, password):
    """
    Compare a passed password by rehashing it comparing it to the stored, hashed password
    """
    return stored_password == hash_password(password)

@app.route("/api/users/")
def get_all_users():
    return json.dumps({"users": DB.get_all_users()}), 200

@app.route("/api/users/testing/")
def get_all_users_testing():
    return json.dumps({"users": DB.get_all_users_testing()}), 200

@app.route("/api/users/", methods=["POST"])
def create_user():
    body = json.loads(request.data)
    name = body.get("name")
    username = body.get("username")
    password = body.get("password")
    balance = body.get("balance", 0)
    email = body.get("email")
    if not name or not username or not password:
        return jsonify({
            "success": False,
            "message": "Name, username, and password are required fields, please pass TEXT into each."
        }), 400
    hashed_password = hash_password(password)
    user_id = DB.insert_user(name, username, hashed_password, balance, email)
    
    user = DB.get_user_by_id(user_id)
    if user is None:
        return jsonify({
            "success": False,
            "message": "User does not exists in the database."
        }), 404
    return json.dumps(user), 201

@app.route("/api/users/email/<int:user_id>/", methods=["POST"])
def change_email(user_id):
    body = json.loads(request.data)
    email = body.get("email")
    if not email or not user_id:
        return jsonify({
            "success": False,
            "message": "please enter an email"
        })
    user = DB.get_user_by_id(user_id)
    if user is None:
        return jsonify({
            "success": False,
            "message": "User does not exists in the database."
        }), 404
    DB.insert_change_email(user_id, email)
    return json.dumps(user), 201


@app.route("/api/users/<int:user_id>/", methods = ["POST"])
def get_user(user_id):
    body = json.loads(request.data)
    password = body.get("password")
    hashed_password = hash_password(password)
    user = DB.get_user_by_id(user_id)
    if user is None:
        return jsonify({
            "success": False,
            "message": "User does not exists in the database or password is incorrect."
        }), 404
    return json.dumps(user), 200

@app.route("/api/users/<int:user_id>/", methods=["DELETE"])
def delete_user(user_id):
    body = json.loads(request.data)
    password = body.get("password")
    hashed_password = hash_password(password)
    user = DB.get_user_by_id(user_id)
    if user is None:
        return jsonify({
            "success": False,
            "message": "The user does not exist or password is wrong and can't be delete"
        }), 404
    DB.delete_user_by_id(user_id)
    return json.dumps(user), 202

def send_money(sender_id=None, receiver_id=None, amount=None, password=None):
    if sender_id is None or receiver_id is None or amount is None or password is None:
        body = json.loads(request.data)
        sender_id = body.get("sender_id")
        receiver_id = body.get("receiver_id")
        amount = body.get("amount")
        password = hash_password(body.get("password"))
    if sender_id is None or receiver_id is None or amount is None or password is None:
        return jsonify({
            "success": False,
            "message": "Specify the sender id, receiver id the amount you want to send, and user password in order to send money."
        }), 400
    sender = DB.get_user_by_id(sender_id)
    if sender is None:
        return jsonify({
            "success": False,
            "message": "The password entered is wrong or null, please enter the correct password."
        })
    sender_balance = sender.get("balance")
    if amount > sender_balance:
        return jsonify({
            "success": False,
            "message": "The sender can't overdraw their balance (amount is greater than sender balance)"
        }), 403
    DB.send_money(sender_id, receiver_id, amount, password)
    return jsonify ({
        "success": True,
        "message": "Successfully transferred funds!"
    })


@app.route("/api/transactions/", methods = ["POST"])
def send_request_transactions():
    body = json.loads(request.data)
    sender_id = body.get("sender_id")
    receiver_id = body.get("receiver_id")
    amount = body.get("amount")
    message = body.get("message")
    accepted = body.get("accepted")
    if not sender_id or not receiver_id:
        return jsonify ({
            "success": False,
            "message": "Please enter a sender and receiver id and a password"
        }), 400
    transaction_id = DB.send_request_money(sender_id, receiver_id, amount, message, accepted)
    this_transaction = DB.get_transaction_by_id(transaction_id)
    if this_transaction is None:
        return jsonify({
            "success": False,
            "message": "Transaction does not exists in the database."
        }), 404
    if accepted is True:
        success = send_money()
        status_code = success.status_code
        if status_code == 400 or status_code == 403:
            return success
    return json.dumps(this_transaction), 202

@app.route("/api/transactions/")
def get_all_transactions():
    return json.dumps({"transactions": DB.get_all_transactions()})

@app.route("/api/transactions/<int:transaction_id>/", methods=["POST"])
def accept_deny_payment_request(transaction_id):
    body = json.loads(request.data)
    accepted = body.get("accepted")
    password = hash_password(body.get("password"))
    target_transaction = DB.get_transaction_by_id(transaction_id)
    if target_transaction["accepted"] is not None:
        return jsonify ({
            "success": False,
            "message": "Cannot change a transaction's accepted field if already handled"
        }), 403
    if target_transaction["accepted"] is None:
        DB.accept_deny_payment_request(transaction_id, accepted)
        target_transaction = DB.get_transaction_by_id(transaction_id)
    if target_transaction["accepted"]==1:
        sender_id = target_transaction["sender_id"]
        receiver_id = target_transaction["receiver_id"]
        amount = target_transaction["amount"]
        success = send_money(sender_id, receiver_id, amount, password)
        status_code = success.status_code
        if status_code == 400 or status_code == 403:
            return success
    return json.dumps(target_transaction), 202

@app.route("/api/users/<int:user_id>/friends/")
def get_friends(user_id):
    user = DB.get_user_by_id(user_id)
    if user is None:
        return jsonify({
            "success": False,
            "message": "This user does not exists"
        }), 404
    return json.dumps({"friends": DB.get_friends(user_id)}), 200

@app.route("/api/users/<int:user_id>/friends/<int:friend_id>/", methods=["POST"])
def create_friendship(user_id, friend_id):
    user = DB.get_user_by_id(user_id)
    friend = DB.get_user_by_id(friend_id)
    if user is None or friend is None:
        return jsonify({
            "success": False,
            "message": "One or both of the users do not exists"
        }), 404
    try:
        DB.create_friendship(user_id, friend_id)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    return jsonify({
        "sucess": True,
        "message": "friendship created!"
    }), 201

@app.route("/api/users/<int:user_id>/transactions/")
def get_transactions_by_user_id(user_id):
    user = DB.get_user_by_id(user_id)
    if user is None:
        return jsonify ({
            "success": False,
            "message": "User does not exist"
        })
    return json.dumps({"transactions": DB.get_transaction_by_user_id(user_id)})

@app.route("/api/users/delete/", methods = ["DELETE"])
def delete_user_table():
    DB.delete_user_table()
    return json.dumps("Table has been deleted")

@app.route("/api/transactions/delete/", methods = ["DELETE"])
def delete_transactions_table():
    DB.delete_transactions_table()
    return json.dumps("Table has been deleted")

@app.route("/api/friends/delete/", methods = ["DELETE"])
def delete_friends_table():
    DB.delete_friends_table()
    return json.dumps("Table has been deleted")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
