import os
from flask import Flask,request, jsonify
from datetime import datetime
import jwt  # PyJWT
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import re

app = Flask(__name__)
public_key_path = os.getenv("PUBLIC_KEY_PATH")

def sanitize_input(input_string):
    """Permette solo caratteri alfanumerici, trattini bassi, spazi e trattini."""
    if not input_string:
        return input_string
    return re.sub(r"[^\w\s-]", "", input_string)
def mock_decode_jwt(token, public_key, algorithms, audience):
    # Simula una risposta di decodifica valida
    if token == "valid_token":
        return {
            "sub": "user1",
            "aud": audience,
            "exp": int(datetime.now().timestamp()) + 3600,  # Token valido per un'ora
            "scope": "user"
        }
    if token == "valid_token2":
        return {
            "sub": "user2",
            "aud": audience,
            "exp": int(datetime.now().timestamp()) + 3600,  # Token valido per un'ora
            "scope": "user"
        }
    if token == "valid_token3":
        return {
            "sub": "user3",
            "aud": audience,
            "exp": int(datetime.now().timestamp()) + 3600  # Token valido per un'ora
        }
    elif token == "expired_token":
        raise jwt.ExpiredSignatureError("Token expired")
    else:
        raise jwt.InvalidTokenError("Invalid token")

def mock_find_balance(username):
    if username == 'not_found':
        return {}
    else: 
        return {
            "username" : username,
            "balance" : 100
        }
    
def mock_newTrans(payer_us,receiver_us,amount, currency, date):
    return {
        'msg' : 'new transaction inserted',
        'payer_us' : payer_us,
        'receiver':receiver_us,
        'amount': amount,
        'currency' : currency,
        'date':date
    }

@app.route('/pay', methods=['POST'])
def pay():
    payer_us = sanitize_input(request.form.get('payer_us'))
    receiver_us = sanitize_input(request.form.get('receiver_us'))
    amount = request.form.get('amount')
    if not amount:
        return jsonify({'Error': 'Invalid amount'}), 400
    if not payer_us:
        return jsonify({'Error': 'Invalid payer_us'}), 400
    if not receiver_us:
        return jsonify({'Error': 'Invalid receiver_us'}), 400

    # Conversion from string to float
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({'Error': 'Invalid amount'}), 400
    if amount<0:
        return jsonify({'Error': 'Invalid amount'}), 400
    

    if payer_us != 'system':
        payer_balance = mock_find_balance(payer_us)
        if not payer_balance:
            return jsonify({'Error': f'Payer user "{payer_us}" not found'}), 404
    if receiver_us != 'system':
        receiver_balance = mock_find_balance(receiver_us)
        if not receiver_balance:
            return jsonify({'Error': f'Receiver user "{receiver_us}" not found'}), 404


    # Controlla che il saldo del pagatore sia sufficiente
    if payer_us!= 'system' and payer_balance['balance'] < amount:
        return jsonify({'Error': 'Balance not sufficient to carry out the operation'}), 422
    # Inserisci una nuova transazione nel database
    
    mock_newTrans(payer_us,receiver_us,amount, "Memecoin", datetime.now())

   
    # Scala i soldi dal saldo del pagatore e aggiungili a quello del ricevente
    if payer_us != "system":
        payer_balance['balance'] -= amount
    if receiver_us != "system":
        receiver_balance['balance'] += amount
    return jsonify({'msg': 'Payment successfully executed'}), 200
 
@app.route('/buycurrency', methods = ['POST'])
def buycurrency():
    data = request.get_json()
    username = sanitize_input(data.get('username'))
    amount = data.get('amount')
    method = sanitize_input(data.get('payment_method'))

    if not amount:
        return jsonify({'Error': 'Invalid amount'}), 400
    if not isinstance(amount, (int, float)):
         return jsonify({"error": "amount must be int or float"}), 400

    # Recupera l'header Authorization
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    access_token = auth_header.removeprefix("Bearer ").strip()

    # Verifica e decodifica del token
    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="payment_service")
        if username and decoded_token.get("sub") != username:
            return jsonify({"error": "Username in token does not match the request username"}), 403
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    if not username:
        return jsonify({'Error': 'Invalid username'}), 400
    if not method:
        return jsonify({'Error': f'Invalid method {method}'}), 400

    # Conversion from string to float
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({'Error': 'Invalid amount'}), 400
    

    #inserisci una transazione nel db 
    paying_t = mock_newTrans(
            payer_us=username,
            receiver_us='system',
            amount=amount,
            currency='Euro',
            date=datetime.now()
        )
    
    receiving_t = mock_newTrans(
            payer_us='system',
            receiver_us=username,
            amount=amount,
            currency='Memecoin',
            date=datetime.now()
        )

    current_balance = mock_find_balance(username)
    if not current_balance:
        return jsonify({'Error': f'Payer user {username} not found'}), 404
    current_balance['balance'] +=amount

    return jsonify({'username': username,'balance':current_balance['balance'],'msg': 'In-game currency purchased successfully'}), 200
mock_transactions_db = [
    {"id": 1, "payer_us": "user1", "receiver_us": "user2", "amount": 100, "currency" : "euro", "date":"11/11/11"},
    {"id": 2, "payer_us": "user3", "receiver_us": "user1", "amount": 50, "currency" : "euro", "date":"11/11/11"},
    {"id": 3, "payer_us": "user2", "receiver_us": "user3", "amount": 200, "currency" : "euro", "date":"11/11/11"},
    {"id": 4, "payer_us": "user1", "receiver_us": "user2", "amount": 75, "currency" : "euro", "date":"11/11/11"},
]

def mock_search_transaction(payer = None, receiver=None):
    if not payer and not receiver:
        return {"error": "At least one of 'payer' or 'receiver' must be specified"}, 400
    
    # Filtra le transazioni in base ai parametri forniti
    if payer:
        result = [t for t in mock_transactions_db if t["payer_us"] == payer]
    elif receiver:
        result = [t for t in mock_transactions_db if t["receiver_us"] == receiver]
    
    # Controlla se sono state trovate transazioni
    if not result:
        return {"error": "No transactions found matching the criteria"}, 404
    return result
@app.route('/viewTrans', methods = ['GET'])
def viewTrans():  
    username = sanitize_input(request.args.get('username'))
    # Recupera l'header Authorization
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    access_token = auth_header.removeprefix("Bearer ").strip()

    # Verifica e decodifica del token
    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="payment_service")
        if decoded_token.get("scope") == "user" and username and decoded_token.get("sub") != username:
            return jsonify({"error": "Username in token does not match the request username"}), 403
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    
    if not username:
        return jsonify({'Error' : 'Invalid parameter username'}), 400
    # Search in the transaction db
    payed_t=mock_search_transaction(payer=username)
    received_t = mock_search_transaction(receiver=username)
    transaction_list = []
    if payed_t:
        result = [{'id': t['id'], 'payer_us': username, 'receiver_us': t['receiver_us'],'amount' : f"-{t['amount']}", 'currency':t['currency'], 'date':t['date']} for t in payed_t]   
        transaction_list += result
    if received_t:
        result = [{'id': t['id'], 'payer_us': t['payer_us'], 'receiver_us': username,'amount' : f"+{t['amount']}", 'currency':t['currency'], 'date':t['date']} for t in received_t]   
        transaction_list += result
    return jsonify(transaction_list), 200

def mock_newBalance(username, balance):
    return {'msg' : 'Balance created',
            'username' : username,
            'balance': balance}
@app.route('/newBalance', methods=['POST'])
def newBalance():
    data = request.get_json()
    username = sanitize_input(data.get('username'))
    if not username:
        return jsonify({"Error" : "Invalid parameter username"}) , 400
    res = mock_find_balance(username)
    if not res:
        mock_newBalance(username, 0)
        return jsonify({'msg': f'Corretcly created a balance for {username}'}), 200
    else:
        return jsonify({'Error': 'Username already inserted in balance db'}), 422

@app.route('/getBalance', methods=['GET'])
def getBalance():
    username = sanitize_input(request.args.get('username'))
    # Recupera l'header Authorization
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    access_token = auth_header.removeprefix("Bearer ").strip()

    # Verifica e decodifica del token
    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="payment_service")
        if decoded_token.get("scope") == "user" and username and decoded_token.get("sub") != username:
            return jsonify({"error": "Username in token does not match the request username"}), 403
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    
    if not username:
        return jsonify({'Error' : 'Invalid parameter username'}), 400
    res = mock_find_balance(username)
    if res: 
        return jsonify({'username': res['username'], 'balance': res['balance']}), 200
    else:
        return jsonify({'Error': 'Not found balance for that user'}), 404
    
@app.route('/deleteBalance', methods=['DELETE'])
def deleteBalance():
    # Recupera l'header Authorization
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    access_token = auth_header.removeprefix("Bearer ").strip()

    # Verifica e decodifica del token
    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="payment_service")
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    data = request.get_json()
    username = sanitize_input(data.get('username'))
    if not username:
        return jsonify({'Error' : 'Invalid parameter username'}), 400
    res = mock_find_balance(username)
    if res:
        return jsonify({'msg': f'Corretcly deleted balance for {username}'}), 200
    else:
        return jsonify({'Error': 'Balance not found'}), 404