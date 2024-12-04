import requests,time
from flask import Flask, request, jsonify
from datetime import datetime
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import os
import re

public_key_path = os.getenv("PUBLIC_KEY_PATH")
app = Flask(__name__)
def mock_payment(payer, receiver , amount):
    return jsonify({'msg': 'Correctly payed'}), 200
def mock_decode_jwt(token, public_key, algorithms, audience):
    # Simula una risposta di decodifica valida
    if token == "valid_token":
        return {
            "sub": "user1",
            "aud": audience,
            "exp": int(datetime.now().timestamp()) + 3600  # Token valido per un'ora
        }
    if token == "valid_token2":
        return {
            "sub": "user2",
            "aud": audience,
            "exp": int(datetime.now().timestamp()) + 3600  # Token valido per un'ora
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

# URL dei servizi

def sanitize_input(input_string):
    """Permette solo caratteri alfanumerici, trattini bassi e spazi."""
    if not input_string:
        return input_string
    return re.sub(r"[^\w\s-]", "", input_string)

def mock_gachasystem(level):
    gacha_details = {
        "gacha_id": "1",
        "gacha_name": "Trial",
        "description":"",
        "rarity": "standard",
        "img": f"https://localhost:5001/images_gacha/uploads/"
    }

    return gacha_details, 200
def mock_profile(gacha):
    return jsonify({"msg" : "gacha correctly received"}),200
@app.route('/gacharoll', methods=['POST'])
def gacharoll():
    # Estrai i dati dal body della richiesta
    data = request.get_json()

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="gacha_roll")  
        #print(f"Token verificato! Dati decodificati: {decoded_token}")
        if 'username' in data and decoded_token.get("sub") != data['username']:
            return jsonify({"error": "Username in token does not match the request username"}), 403
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    # Controlla che i parametri siano presenti
    if 'username' not in data or 'level' not in data:                               
        return jsonify({"error": "Missing 'username' or 'level' parameter"}), 400
    
    username = sanitize_input(data['username'])
    level = sanitize_input(data['level'])

    # Determina l'importo in base al livello
    if level == "standard":
        amount = 10
    elif level == "medium":
        amount = 20
    elif level == "premium":
        amount = 40
    else:
        return jsonify({"error": "Invalid level parameter"}), 400


    payment_response,status = mock_payment(username, "system", amount)
    # try: 
    #     payment_response = requests.post(PAYMENT_SERVICE_URL, data=payment_data, timeout=10)
    if status != 200:
        return jsonify({"error": f"Payment failed , details : {payment_response}"}), status
    # params={'level': level}
    response,status = mock_gachasystem(level)
    # try:
    #     # Step 2: Fai una chiamata al servizio Gacha System per ottenere il Gacha (roll)
    #     response = requests.get(GACHA_SYSTEM_URL, params={'level': level}, timeout=10)
    if status != 200:
        return jsonify({"error": f"Failed to fetch gacha from gachasystem, details : {response}"}), status

    # Estrai il gacha dal servizio Gacha System
    gacha = response

    # Step 3: Ottieni la data attuale (collected_date) come oggetto datetime
    collected_date = datetime.now()  # Oggetto datetime, non stringa

    # Step 4: Inserisci il gacha nel profilo dell'utente (chiamata a profile_setting)
    gacha_data = {
        "username": username,
        "gacha_name": gacha['gacha_name'],  
        "collected_date": collected_date.isoformat()  # Passiamo l'oggetto datetime
    }
    profile_response = mock_profile(gacha_data)
    # try:
    #     profile_response = requests.post(PROFILE_SETTING_URL, json=gacha_data, timeout=10)
    if status != 200:
        return jsonify({"error": f"Failed to insert gacha into user profile , details {profile_response}"}), status

    # Ritorna il risultato del gacha
    return jsonify({
        "gacha_name": gacha['gacha_name'],
        "description": gacha['description'],
        "rarity": gacha['rarity'],
        "img": gacha['img'],
        "collected_date": collected_date.isoformat()  # Includi la data come stringa nel formato ISO
    }), 200

#if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=5007)  # La porta 5007 è quella su cui il servizio è esposto
