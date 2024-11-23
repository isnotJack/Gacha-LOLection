from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import requests , time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@auth_db:5432/auth_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
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
            self._fail()
            return {'Error': error_content}, response.status_code

        except requests.exceptions.RequestException as e:
            # Per errori di connessione o altri problemi
            self._fail()
            return {'Error': f'Error calling the service: {str(e)}'}, response.status_code


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
auth_circuit_breaker = CircuitBreaker()


# Modello Utente
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)

# Endpoint per la creazione di un account
@app.route('/signup', methods=['POST'])
def signup():
    #Dati arrivano in formato JSON dal gateway
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password or not email:
        return jsonify({"Error": "Missing parameters"}), 400
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'Error': f'User {username} already present'}), 422   
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password, email=email, role= 'user')

    db.session.add(new_user)
    db.session.commit()
    # Chiamata al servizio `profile_setting` per creare il profilo
    params = {
        'username': username,
        'profile_image': 'default_image_url',
        'currency_balance': 0
    }
    url = 'http://profile_setting:5003/create_profile'
    # x = requests.post(url, json=params, timeout=10)
    res, status = auth_circuit_breaker.call('post', url, params, {},{}, True )
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
    x , status = auth_circuit_breaker.call('post', url, params, {},{},True)
    if status != 200:
        # Ritorna un errore se la chiamata al `profile_setting` fallisce
        return jsonify({'Error': f'Failed to create profile: {x}'}), 500 
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
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity={'username': username, 'role': 'user'})
        return jsonify(access_token=access_token), 200
    return jsonify({"Error": "Invalid credentials"}), 422


# Endpoint per il logout (simulato, senza revoca token per semplicità)
@app.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    return jsonify({"msg": "Logout success"}), 200

# Endpoint per l'eliminazione di un account
@app.route('/delete', methods=['DELETE'])
def delete_account():
    #Dati arrivano in formato JSON dal gateway
    data = request.get_json()
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
        res, status = auth_circuit_breaker.call('delete', url, params, {},{}, True)
        if status != 200:
            # Ritorna un errore se la chiamata al `profile_setting` fallisce
            return jsonify({'Error': f'Failed to delete profile: {res}'}), 500
        url = 'http://payment_service:5006/deleteBalance'
            # x = requests.delete(url, json=params, timeout=10)
            # x.raise_for_status()
            # res = x.json()
        res, status = auth_circuit_breaker.call('delete', url, params, {},{}, True)
        if status != 200:
            return jsonify({'Error': f'Failed to delete balance: {res}'}), 500
        return jsonify({"msg": "Account deleted successfully"}), 200
    else:
        return jsonify({"Error": "User not found or incorrect password"}), 404

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5001)
