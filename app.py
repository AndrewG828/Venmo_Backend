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
    return json.dumps({"tasks": DB.get_all_users()}), 200

@app.route("/api/users/", methods=["POST"])
def create_user():
    body = json.loads(request.data)
    name = body.get("name")
    username = body.get("username")
    password = body.get("password")
    balance = body.get("balance", 0)
    if not name or not username or not password:
        return jsonify({
            "success": False,
            "message": "Name, username, and password are required fields, please pass TEXT into each."
        }), 400
    hashed_password = hash_password(password)
    user_id = DB.insert_user(name, username, hashed_password, balance)
    
    user = DB.get_user_by_id(user_id, hashed_password)
    if user is None:
        return jsonify({
            "success": False,
            "message": "User does not exists in the database."
        }), 404
    return json.dumps(user), 201


@app.route("/api/user/<int:user_id>/", methods = ["POST"])
def get_user(user_id):
    body = json.loads(request.data)
    password = body.get("password")
    hashed_password = hash_password(password)
    user = DB.get_user_by_id(user_id, hashed_password)
    if user is None:
        return jsonify({
            "success": False,
            "message": "User does not exists in the database or password is incorrect."
        }), 404
    return json.dumps(user), 200

@app.route("/api/user/<int:user_id>/", methods=["DELETE"])
def delete_user(user_id):
    body = json.loads(request.data)
    password = body.get("password")
    hashed_password = hash_password(password)
    user = DB.get_user_by_id(user_id, hashed_password)
    if user is None:
        return jsonify({
            "success": False,
            "message": "The user does not exist or password is wrong and can't be delete"
        }), 404
    DB.delete_user_by_id(user_id)
    return json.dumps(user), 202

@app.route("/api/send/", methods = ["POST"])
def send_money():
    body = json.loads(request.data)
    sender_id = body.get("sender_id")
    receiver_id = body.get("receiver_id")
    amount = body.get("amount")
    password = body.get("password")
    if sender_id is None or receiver_id is None or amount is None or password is None:
        return jsonify({
            "success": False,
            "message": "Specify the sender id, receiver id the amount you want to send, and user password in order to send money."
        }), 400
    hashed_password = hash_password(password)
    sender = DB.get_user_by_id(sender_id, hashed_password)
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
        }), 400
    DB.send_money(sender_id, receiver_id, amount, hashed_password)
    return jsonify ({
        "success": True,
        "message": "Successfully transferred funds!"
    })

@app.route("/api/delete/", methods = ["DELETE"])
def delete_table():
    DB.delete_user_table()
    return json.dumps("Table has been deleted")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
