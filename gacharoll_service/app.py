import requests
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# URL dei servizi
GACHA_SYSTEM_URL = "http://gachasystem:5004/get_gacha_roll"  # Nome del container nel docker-compose
PAYMENT_SERVICE_URL = "http://payment_service:5006/pay"  # Nome del container nel docker-compose
PROFILE_SETTING_URL = "http://profile_setting:5003/insertGacha"  # Nome del container nel docker-compose

@app.route('/gacharoll', methods=['POST'])
def gacharoll():
    # Estrai i dati dal body della richiesta
    data = request.get_json()

    # Controlla che i parametri siano presenti
    if 'username' not in data or 'level' not in data:                               
        return jsonify({"error": "Missing 'username' or 'level' parameter"}), 400

    username = data['username']
    level = data['level']

    # Determina l'importo in base al livello
    if level == "standard":
        amount = 10
    elif level == "medium":
        amount = 20
    elif level == "premium":
        amount = 40
    else:
        return jsonify({"error": "Invalid level parameter"}), 400

    # Step 1: Fai una chiamata al servizio di pagamento
    payment_data = {
        "payer_us": username,
        "receiver_us": "system",
        "amount": amount
    }

    payment_response = requests.post(PAYMENT_SERVICE_URL, data=payment_data)

    if payment_response.status_code != 200:
        return jsonify({"error": "Payment failed"}), 500

    # Step 2: Fai una chiamata al servizio Gacha System per ottenere il Gacha (roll)
    response = requests.get(GACHA_SYSTEM_URL, params={'level': level})

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch gacha from gachasystem"}), 500

    # Estrai il gacha dal servizio Gacha System
    gacha = response.json()

    # Step 3: Ottieni la data attuale (collected_date) come oggetto datetime
    collected_date = datetime.now()  # Oggetto datetime, non stringa

    # Step 4: Inserisci il gacha nel profilo dell'utente (chiamata a profile_setting)
    gacha_data = {
        "username": username,
        "gacha_name": gacha['gacha_name'],  
        "collected_date": collected_date.isoformat()  # Passiamo l'oggetto datetime
    }

    profile_response = requests.post(PROFILE_SETTING_URL, json=gacha_data)

    if profile_response.status_code != 200:
        return jsonify({"error": "Failed to insert gacha into user profile"}), 500

    # Ritorna il risultato del gacha
    return jsonify({
        "gacha_name": gacha['gacha_name'],
        "description": gacha['description'],
        "rarity": gacha['rarity'],
        "img": gacha['img'],
        "collected_date": collected_date.isoformat()  # Includi la data come stringa nel formato ISO
    }), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5007)  # La porta 5007 è quella su cui il servizio è esposto
