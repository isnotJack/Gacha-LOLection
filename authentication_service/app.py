from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
# from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import bcrypt
import requests , time
import os
import datetime
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@auth_db:5432/auth_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

private_key_path = os.getenv("PRIVATE_KEY_PATH")
public_key_path = os.getenv("PUBLIC_KEY_PATH")

db = SQLAlchemy(app)
# bcrypt = Bcrypt(app)
#jwt = JWTManager(app)
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
profile_circuit_breaker = CircuitBreaker()
payment_circuit_breaker = CircuitBreaker()


# Modello Utente
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    salt = db.Column(db.String(200), nullable=False)  # Nuovo campo per il salt
    role = db.Column(db.String(50), nullable=False)

class RefreshToken(db.Model):
    __tablename__ = 'refresh_tokens'
    jti_id = db.Column(db.String(200), primary_key=True)
    is_revoked = db.Column(db.Boolean, nullable=False)

# Endpoint per la creazione di un account
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    auth = request.headers.get('Origin')
    if not auth or auth != 'admin_gateway':
        role='user'
    else:
        role='admin'
    if not username or not password or not email:
        return jsonify({"Error": "Missing parameters"}), 400
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'Error': f'User {username} already present'}), 422   
    salt = bcrypt.gensalt().decode('utf-8')  # Genera il salt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt.encode('utf-8')).decode('utf-8')
    
    # Creazione del nuovo utente
    new_user = User(username=username, password=hashed_password, role=role, salt=salt)

    db.session.add(new_user)
    db.session.commit()
    
    # Chiamata al servizio `profile_setting` per creare il profilo
    params = {
        'username': username,
        'email': email,
        'profile_image': 'default_image_url',
        'currency_balance': 0
    }
    url = 'http://profile_setting:5003/create_profile'
    # x = requests.post(url, json=params, timeout=10)
    res, status = profile_circuit_breaker.call('post', url, params, {},{}, True )
    # x.raise_for_status()
    # res = x.json()
    if status != 200:
        # Ritorna un errore se la chiamata al `profile_setting` fallisce
        return jsonify({'Error': f'Failed to create profile: {res}'}), 500
    params = {
        'username': username,
    }
    url = 'http://payment_service:5006/newBalance'
    
        # y = requests.post(url, json=params, timeout=10)
        # y.raise_for_status()
        # res = x.json()
    x , status = payment_circuit_breaker.call('post', url, params, {},{},True)
    if status != 200:
        # Ritorna un errore se la chiamata al `profile_setting` fallisce
        return jsonify({'Error': f'Failed to create user balance: {x}'}), 500 
    return jsonify({"msg": "Account created successfully", "profile_message": res.get('message')}), 200


# Endpoint per il login
@app.route('/login', methods=['POST'])
def login():
      #Dati arrivano in formato JSON dal gateway
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
         return jsonify({"Error": "Missing parameters"}), 400
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"Error": "User not found"}), 404
    
    hashed_input = bcrypt.hashpw(password.encode('utf-8'), user.salt.encode('utf-8')).decode('utf-8')
    if user.password == hashed_input:
        # Legge la chiave privata
        with open(private_key_path, "r") as key_file:
            private_key = key_file.read()

        if user.role == "user":
            scope = "user"
        else:
            scope = "admin" 
        jti = str(uuid.uuid4())  # Genera un UUID univoco per il jti

        header = { 
            "alg": "RS256",
            "typ": "JWT"
        } 
        payload = {
            "iss": "http://auth_service:5002",      # Emittente
            "sub": user.username,              # Soggetto
            "aud": ["profile_setting", "gachasystem", "payment_service", "gacha_roll", "auction_service"],         
            "iat": datetime.datetime.now(datetime.timezone.utc),  # Issued At
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5),  # Expiration
            "scope": scope,                   # Scopi
            "jti": jti              # JWT ID
        }

        access_token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)

        refresh_jti = str(uuid.uuid4())  # Genera un UUID univoco per il jti

        header = {
            "alg": "RS256",
            "typ": "JWT"
        }

        payload = {
            "iss": "http://auth_service:5002",      # Emittente
            "sub": user.username,                  # Soggetto (può essere l'ID utente o l'email)
            "iat": datetime.datetime.now(datetime.timezone.utc),  # Issued At
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),  # Expiration (7 giorni)
            "jti": refresh_jti                             # JWT ID
        }

        refresh_token = jwt.encode(payload, private_key, algorithm="RS256", headers=header)
        new_token = RefreshToken(jti_id=refresh_jti, is_revoked = False)
        db.session.add(new_token)
        db.session.commit()
        return jsonify(access_token=access_token, refresh_token = refresh_token), 200
    return jsonify({"Error": "Invalid credentials"}), 422


# Endpoint per il logout (simulato, senza revoca token per semplicità)
@app.route('/logout', methods=['DELETE'])
def logout():
    ref_token = request.headers.get('Authorization')
    if not ref_token:
        return jsonify({"error": "Missing Authorization header"}), 401
    ref_token = ref_token.removeprefix("Bearer ").strip()
    # try:
    # Carica la chiave pubblica
    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()
    
    # Decodifica il token
    decoded_token = jwt.decode(ref_token, public_key, algorithms=["RS256"])
    jti = decoded_token.get("jti")  # Estrai il jti dal token
    
    # Cerca il token nel database
    old_token = RefreshToken.query.filter_by(jti_id=jti).first()
    if not old_token:
        return jsonify({'error': 'Refresh token not found'}), 404

    # Controlla se il token è già scaduto
    if old_token.is_revoked:
        return jsonify({"msg": "Token already revoked"}), 200

    # Marca il token come scaduto
    old_token.is_revoked = True
    db.session.commit()

    return jsonify({"msg": "Logout success"}), 200

    # except jwt.ExpiredSignatureError:
    #     return jsonify({"error": "Refresh token expired"}), 401
    # except jwt.InvalidTokenError:
    #     return jsonify({"error": "Invalid token"}), 400
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500
# Endpoint per l'eliminazione di un account
@app.route('/delete', methods=['DELETE'])
def delete_account():
    data = request.get_json()
    #Dati arrivano in formato JSON dal gateway
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
    username = data.get('username')
    password = data.get('password') 
    if not username or not password:
        return jsonify({'Error': 'Missing parameters'}),400
    
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        db.session.delete(user)
        db.session.commit()
        # Chiamata al servizio `profile_setting` per eliminare il profilo
        params = {
            'username': username,
        }
        url = 'http://profile_setting:5003/delete_profile'
            # x = requests.delete(url, json=params, timeout=10)
            # x.raise_for_status()
            # res = x.json()
        headers={
            'Authorization' : f'Bearer {access_token}'
        }
        res, status = profile_circuit_breaker.call('delete', url, params, headers,{}, True)
        if status != 200:
            # Ritorna un errore se la chiamata al `profile_setting` fallisce
            return jsonify({'Error': f'Failed to delete profile: {res}'}), 500
        url = 'http://payment_service:5006/deleteBalance'
            # x = requests.delete(url, json=params, timeout=10)
            # x.raise_for_status()
            # res = x.json()
        res, status = payment_circuit_breaker.call('delete', url, params, headers,{}, True)
        if status != 200:
            return jsonify({'Error': f'Failed to delete balance: {res}'}), 500
        return jsonify({"msg": "Account deleted successfully"}), 200
    else:
        return jsonify({"Error": "User not found or incorrect password"}), 404

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5001)
