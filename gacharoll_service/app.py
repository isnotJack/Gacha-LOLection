import requests,time
from flask import Flask, request, jsonify
from datetime import datetime
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import os

app = Flask(__name__)

# URL dei servizi
GACHA_SYSTEM_URL = "http://gachasystem:5004/get_gacha_roll"  # Nome del container nel docker-compose
PAYMENT_SERVICE_URL = "http://payment_service:5006/pay"  # Nome del container nel docker-compose
PROFILE_SETTING_URL = "http://profile_setting:5003/insertGacha"  # Nome del container nel docker-compose

public_key_path = os.getenv("PUBLIC_KEY_PATH")

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=5, reset_timeout=10):
        self.failure_threshold = failure_threshold  # Soglia di fallimento
        self.recovery_timeout = recovery_timeout      # Tempo di recupero tra i tentativi
        self.reset_timeout = reset_timeout          # Tempo massimo di attesa prima di ripristinare il circuito
        self.failure_count = 0                      # Numero di fallimenti consecutivi
        self.last_failure_time = 0                  # Ultimo tempo in cui si è verificato un fallimento
        self.state = 'CLOSED'                       # Stato iniziale del circuito (CLOSED)

    def call(self, method, url, params=None, headers=None, files=None, json=True):
        if self.state == 'OPEN':
            # Se il circuito è aperto, controlla se è il momento di provare di nuovo
            if time.time() - self.last_failure_time > self.reset_timeout:
                print("Closing the circuit")
                self.state = 'CLOSED'
                self._reset()
            else:
                return jsonify({'Error': 'Open circuit, try again later'}), 503  # ritorna un errore 503

        try:
            # Usa requests.request per specificare il metodo dinamicamente
            if json:
                response = requests.request(method, url, json=params, headers=headers)
            else:
                response = requests.request(method, url, data=params, headers=headers, files=files)
            
            response.raise_for_status()  # Solleva un'eccezione per errori HTTP (4xx, 5xx)

            # Verifica se la risposta è un'immagine
            if 'image' in response.headers.get('Content-Type', ''):
                return response.content, response.status_code  # Restituisce il contenuto dell'immagine

            return response.json(), response.status_code  # Restituisce il corpo della risposta come JSON

        except requests.exceptions.HTTPError as e:
            # In caso di errore HTTP, restituisci il contenuto della risposta (se disponibile)
            error_content = response.text if response else str(e)
            # self._fail()
            return {'Error': error_content}, response.status_code

        except requests.exceptions.ConnectionError as e:
            # Per errori di connessione o altri problemi
            self._fail()
            return {'Error': f'Error calling the service: {str(e)}'}, 503

    def _fail(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            print("Circuito aperto a causa di troppi errori consecutivi.")
            self.state = 'OPEN'

    def _reset(self):
        self.failure_count = 0
        self.state = 'CLOSED'

# Inizializzazione dei circuit breakers
gacha_sys_circuit_breaker = CircuitBreaker()
profile_circuit_breaker = CircuitBreaker()
payment_circuit_breaker = CircuitBreaker()

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
        decoded_token = jwt.decode(access_token, public_key, algorithms=["RS256"], audience="gacha_roll")  
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

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    payment_response,status = payment_circuit_breaker.call('post', PAYMENT_SERVICE_URL, payment_data, headers,{}, False)
    # try: 
    #     payment_response = requests.post(PAYMENT_SERVICE_URL, data=payment_data, timeout=10)
    if status != 200:
        return jsonify({"error": f"Payment failed , details : {payment_response}"}), status
    # params={'level': level}
    url = GACHA_SYSTEM_URL + f'?level={level}'
    response,status = gacha_sys_circuit_breaker.call('get', url, {}, headers, {}, False)
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
    profile_response = profile_circuit_breaker.call('post', PROFILE_SETTING_URL, gacha_data,headers,{}, True)
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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5007)  # La porta 5007 è quella su cui il servizio è esposto
