from flask import Flask, request, jsonify
# from flask_sqlalchemy import SQLAlchemy
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
# from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import bcrypt
import requests , time
import os
import datetime
import uuid
import re  # Per sanitizzare input


app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@auth_db:5432/auth_db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config['JWT_SECRET_KEY'] = 'super-secret-key'

private_key_path = os.getenv("PRIVATE_KEY_PATH")
public_key_path = os.getenv("PUBLIC_KEY_PATH")

# db = SQLAlchemy(app)
# bcrypt = Bcrypt(app)
#jwt = JWTManager(app)
# class CircuitBreaker:
#     def __init__(self, failure_threshold=3, recovery_timeout=5, reset_timeout=10):
#         self.failure_threshold = failure_threshold  # Soglia di fallimento
#         self.recovery_timeout = recovery_timeout      # Tempo di recupero tra i tentativi
#         self.reset_timeout = reset_timeout          # Tempo massimo di attesa prima di ripristinare il circuito
#         self.failure_count = 0                      # Numero di fallimenti consecutivi
#         self.last_failure_time = 0                  # Ultimo tempo in cui si è verificato un fallimento
#         self.state = 'CLOSED'                       # Stato iniziale del circuito (CLOSED)

#     def call(self, method, url, params=None, headers=None, files=None, json=True):
#         if self.state == 'OPEN':
#             # Se il circuito è aperto, controlla se è il momento di provare di nuovo
#             if time.time() - self.last_failure_time > self.reset_timeout:
#                 print("Closing the circuit")
#                 self.state = 'CLOSED'
#                 self._reset()
#             else:
#                 return jsonify({'Error': 'Open circuit, try again later'}), 503  # ritorna un errore 503

#         try:
#             # Usa requests.request per specificare il metodo dinamicamente
#             if json:
#                 response = requests.request(method, url, json=params, headers=headers, verify=False)
#             else:
#                 response = requests.request(method, url, data=params, headers=headers, files=files, verify=False)
            
#             response.raise_for_status()  # Solleva un'eccezione per errori HTTP (4xx, 5xx)

#             # Verifica se la risposta è un'immagine
#             if 'image' in response.headers.get('Content-Type', ''):
#                 return response.content, response.status_code  # Restituisce il contenuto dell'immagine
#             return response.json(), response.status_code  # Restituisce il corpo della risposta come JSON

#         except requests.exceptions.HTTPError as e:
#             # In caso di errore HTTP, restituisci il contenuto della risposta (se disponibile)
#             error_content = response.text if response else str(e)
#             # self._fail()
#             return {'Error': error_content}, response.status_code

#         except requests.exceptions.ConnectionError as e:
#             # Per errori di connessione o altri problemi
#             self._fail()
#             return {'Error': f'Error calling the service: {str(e)}'}, 503


#     def _fail(self):
#         self.failure_count += 1
#         self.last_failure_time = time.time()
#         if self.failure_count >= self.failure_threshold:
#             print("Circuito aperto a causa di troppi errori consecutivi.")
#             self.state = 'OPEN'

#     def _reset(self):
#         self.failure_count = 0
#         self.state = 'CLOSED'


# # Inizializzazione dei circuit breakers
# profile_circuit_breaker = CircuitBreaker()
# payment_circuit_breaker = CircuitBreaker()

# Funzione per sanitizzare input
def sanitize_input(input_string):
    """Permette solo caratteri alfanumerici, trattini bassi e spazi"""
    if not input_string:
        return input_string
    return re.sub(r"[^\w\s\-]", "", input_string)

def sanitize_input_error(input_string):
    """Permette solo caratteri alfanumerici, trattini bassi e spazi"""
    if not input_string:
        return input_string  # Ritorna direttamente se l'input è vuoto o None
    
    # Controlla se l'input contiene caratteri non validi
    invalid_chars = re.search(r"[^\w\s]", input_string)
    if invalid_chars:
        return True

# Funzione per validare email
def validate_email(email):
    """Conferma che l'email sia in un formato valido"""
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_regex, email)



# Modello Utente
# class User(db.Model):
#     __tablename__ = 'users'
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(50), unique=True, nullable=False)
#     password = db.Column(db.String(100), nullable=False)
#     salt = db.Column(db.String(200), nullable=False)  # Nuovo campo per il salt
#     role = db.Column(db.String(50), nullable=False)

# class RefreshToken(db.Model):
#     __tablename__ = 'refresh_tokens'
#     jti_id = db.Column(db.String(200), primary_key=True)
#     is_revoked = db.Column(db.Boolean, nullable=False)

from flask import jsonify, request
import bcrypt

# Funzione per simulare la creazione dell'utente nel database
def mock_create_user(username, password, role, salt):
    # Simula un utente creato correttamente
    return {
        'username': username,
        'password': password,
        'role': role,
        'salt': salt
    }

# Funzione per simulare la risposta del servizio profile_setting
def mock_call_profile_service(username, email):
    # Simula una risposta di successo dal servizio profile_setting
    return {'message': 'Profile created successfully'}, 200

# Funzione per simulare la risposta del servizio payment_service
def mock_call_payment_service(username):
    # Simula una risposta di successo dal servizio payment_service
    return {'message': 'Balance created successfully'}, 200

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = sanitize_input(data.get('username'))
    password = data.get('password')
    email = data.get('email')

    # Validazione email
    if not validate_email(email):
        return jsonify({"Error": "Invalid email format"}), 400

    # Determina il ruolo dell'utente in base all'header
    auth = request.headers.get('Origin')
    if not auth or auth != 'admin_gateway':
        role = 'user'
    else:
        role = 'admin'

    # Verifica che i parametri obbligatori siano presenti
    if not username or not password or not email:
        return jsonify({"Error": "Missing parameters"}), 400

    # Simula un controllo se l'utente esiste già nel database
    # In un vero contesto, questa parte interagirebbe con il database
    if username == "existing_user":  # Aggiungi un caso di test per un utente esistente
        return jsonify({'Error': f'User {username} already present'}), 422

    # Genera il salt e l'hash della password
    salt = bcrypt.gensalt().decode('utf-8')  # Genera il salt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt.encode('utf-8')).decode('utf-8')

    # Simula la creazione dell'utente (senza interagire con il database)
    new_user = mock_create_user(username, hashed_password, role, salt)

    # Simula la chiamata al servizio profile_setting per creare il profilo
    res, status = mock_call_profile_service(username, email)
    if status != 200:
        return jsonify({'Error': f'Failed to create profile: {res}'}), 500

    # Simula la chiamata al servizio payment_service per creare il bilancio
    x, status = mock_call_payment_service(username)
    if status != 200:
        return jsonify({'Error': f'Failed to create user balance: {x}'}), 500

    # Ritorna la risposta finale con il successo
    return jsonify({"msg": "Account created successfully", "profile_message": res.get('message')}), 200

# Funzione mock per simulare la ricerca dell'utente nel database
def mock_get_user(username):
    # Simula un utente trovato nel database
    salt = bcrypt.gensalt().decode('utf-8')
    if username == "user1":
        return {
            'username': 'user1',
            'password': bcrypt.hashpw("1234".encode('utf-8'),salt.encode('utf-8')).decode('utf-8'),
            'salt': salt,
            'role': 'user'
        }
    if username == "admin1":
        return {
            'username': 'admin1',
            'password': bcrypt.hashpw("1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            'salt': bcrypt.gensalt().decode('utf-8'),
            'role': 'admin'
        }
    return None  # Simula utente non trovato

# Funzione mock per simulare la creazione di un refresh token nel database
def mock_create_refresh_token(refresh_jti):
    # Simula l'aggiunta di un refresh token al database (nessuna logica reale)
    return {'jti': refresh_jti, 'is_revoked': False}

# Funzione mock per simulare la lettura della chiave privata
def mock_read_private_key():
    # Simula la lettura di una chiave privata (è una stringa fittizia)
    return "mock-private-key"
# Funzione mock per simulare la lettura della chiave privata
def mock_read_public_key():
    # Simula la lettura di una chiave privata (è una stringa fittizia)
    return "mock-public-key"

@app.route('/login', methods=['POST'])
def login():
    # Dati arrivano in formato JSON dal gateway
    data = request.get_json()
    username = sanitize_input(data.get('username'))
    password = data.get('password')
    
    if not username or not password:
         return jsonify({"Error": "Missing parameters"}), 400
    
    # Simula la ricerca dell'utente nel database
    user = mock_get_user(username)
    if not user:
        return jsonify({"Error": "User not found"}), 404

    # Verifica se la password è corretta
    hashed_input = bcrypt.hashpw(password.encode('utf-8'), user['salt'].encode('utf-8')).decode('utf-8')
    if user['password'] == hashed_input:
        with open(private_key_path, "r") as key_file:
            private_key = key_file.read()

        # Determina il ruolo dell'utente
        if user['role'] == "user":
            scope = "user"
        else:
            scope = "admin"

        # Crea il payload e l'header del token di accesso
        jti = str(uuid.uuid4())  # Genera un UUID univoco per il jti
        header = { 
            "alg": "RS256",
            "typ": "JWT"
        }
        payload = {
            "iss": "https://auth_service:5002",      # Emittente
            "sub": user['username'],                # Soggetto
            "aud": ["profile_setting", "gachasystem", "payment_service", "gacha_roll", "auction_service", "auth_service"],         
            "iat": datetime.datetime.now(datetime.timezone.utc),  # Issued At
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5),  # Expiration
            "scope": scope,                          # Scopi
            "jti": jti                               # JWT ID
        }
        access_token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)

        # Crea il payload e l'header del refresh token
        refresh_jti = str(uuid.uuid4())  # Genera un UUID univoco per il jti
        header = {
            "alg": "RS256",
            "typ": "JWT"
        }
        payload = {
            "iss": "https://auth_service:5002",      # Emittente
            "sub": user['username'],                 # Soggetto (può essere l'ID utente o l'email)
            "aud": "auth_service",
            "iat": datetime.datetime.now(datetime.timezone.utc),  # Issued At
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),  # Expiration
            "scope": scope,
            "jti": refresh_jti                      # JWT ID
        }
        refresh_token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)

        # Simula la creazione di un nuovo refresh token nel database
        mock_create_refresh_token(refresh_jti)

        # Restituisce i token di accesso e di refresh
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200

    return jsonify({"Error": "Invalid credentials"}), 422


def mock_search_token(jti):
    return {
        'jti' : jti,
        'is_revoked': False
    }

def mock_revocking_token(old_token):
    return "Token revoked"

# Endpoint per il logout (simulato, senza revoca token per semplicità)
@app.route('/logout', methods=['DELETE'])
def logout():
    ref_token = request.headers.get('Authorization')
    if not ref_token:
        return jsonify({"error": "Missing Authorization header"}), 401
    ref_token = ref_token.removeprefix("Bearer ").strip()
    try:
        with open(public_key_path, "r") as key_file:
            public_key = key_file.read()

        # Decodifica il token
        decoded_token = jwt.decode(ref_token, public_key, algorithms=["RS256"], audience="auth_service")
        jti = decoded_token.get("jti")  # Estrai il jti dal token

        old_token =mock_search_token(jti)
        if not old_token:
            return jsonify({'error': 'Refresh token not found'}), 404

        # Controlla se il token è già scaduto
        if old_token['is_revoked']:
            return jsonify({"msg": "Token already revoked"}), 200

        mock_revocking_token(old_token)

        return jsonify({"msg": "Logout success"}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Refresh token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Endpoint per l'eliminazione di un account

def mock_delete_profile(username):
    return jsonify({'message': 'Profile deleted correctly'}), 200

def mock_delete_balance(username):
    return jsonify({'message': 'Balance deleted correctly'}), 200


@app.route('/delete', methods=['DELETE'])
def delete_account():
    data = request.get_json()
    #Dati arrivano in formato JSON dal gateway
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 400
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = jwt.decode(access_token, public_key, algorithms=["RS256"], audience="auth_service")  
        #print(f"Token verificato! Dati decodificati: {decoded_token}")
        if 'username' in data and decoded_token.get("sub") != data['username']:
            return jsonify({"error": "Username in token does not match the request username"}), 403
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    username = sanitize_input(data.get('username'))
    password = data.get('password') 
    if not username or not password:
        return jsonify({'Error': 'Missing parameters'}),400
    
    user = mock_get_user(username)
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        # db.session.delete(user)
        # db.session.commit()
        # Chiamata al servizio `profile_setting` per eliminare il profilo
        
        res, status = mock_delete_profile(username)
        if status != 200:
            return jsonify({'Error': f'Failed to delete profile: {res}'}), 500
        url = 'https://payment_service:5006/deleteBalance'
            
        res, status = mock_delete_balance(username)
        if status != 200:
            return jsonify({'Error': f'Failed to delete balance: {res}'}), 500
        return jsonify({"msg": "Account deleted successfully"}), 200
    else:
        return jsonify({"Error": "User not found or incorrect password"}), 404


@app.route('/newToken', methods=['GET'])
def newToken():
    ref_token = request.headers.get('Authorization')
    if not ref_token:
        return jsonify({'error': 'Refresh token not present'}), 400
    ref_token = ref_token.removeprefix("Bearer ").strip()

    try:
        with open(public_key_path, 'r') as key_file:
            public_key = key_file.read()
        # Decodifica il token
        decoded_token = jwt.decode(ref_token, public_key, algorithms=["RS256"], audience="auth_service")
        jti = decoded_token.get("jti")  # Estrai il jti dal token
        
        old_token = mock_search_token(jti)
        if not old_token:
            return jsonify({'error': 'Refresh token not found'}), 404

        # Controlla se il token è già scaduto
        if old_token['is_revoked']:
            return jsonify({"msg": "Token already revoked"}), 500
        with open(private_key_path, "r") as priv_key_file:
            private_key = priv_key_file.read()

        jti = str(uuid.uuid4())  # Genera un UUID univoco per il jti

        header = { 
            "alg": "RS256",
            "typ": "JWT"
        } 
        payload = {
            "iss": "https://auth_service:5002",      # Emittente
            "sub": decoded_token.get("sub"),              # Soggetto
            "aud": ["profile_setting", "gachasystem", "payment_service", "gacha_roll", "auction_service", "auth_service"],         
            "iat": datetime.datetime.now(datetime.timezone.utc),  # Issued At
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5),  # Expiration
            "scope": decoded_token.get("scope"),                   # Scopi
            "jti": jti              # JWT ID
        }

        access_token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)
        return jsonify(access_token=access_token) , 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Refresh token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    db.create_all()
    #app.run(host='0.0.0.0', port=5001)
