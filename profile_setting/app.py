from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import requests
import os, time
from requests.exceptions import ConnectionError, HTTPError
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@profile_db:5432/profile_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

UPLOAD_FOLDER = '/app/static/uploads'  # Percorso dove Docker monta il volume
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}  # Estensioni permesse

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
                print("Circuito mezzo aperto, tentando...")
                self.state = 'HALF_OPEN'
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
profile_circuit_breaker = CircuitBreaker()

# Modello per il profilo utente
class Profile(db.Model):
    __tablename__ = 'profiles'
    username = db.Column(db.String(50), primary_key=True)
    profile_image = db.Column(db.String(200), nullable=True)
    currency_balance = db.Column(db.Integer, default=0)
    gacha_collection = db.relationship('GachaItem', backref='profile' , lazy=True)

# Modello per gli oggetti gacha
class GachaItem(db.Model):
    __tablename__ = 'gacha_items'
    gacha_name = db.Column(db.String(100), nullable=False)
    collected_date = db.Column(db.DateTime(50), nullable=False)  
    username = db.Column(db.String(50), db.ForeignKey('profiles.username', ondelete='CASCADE'), nullable=False)
    # Definizione della chiave primaria composta
    __table_args__ = (
        db.PrimaryKeyConstraint('gacha_name', 'collected_date'),
    )

# Endpoint per modificare il profilo
@app.route('/modify_profile', methods=['PATCH'])
#@jwt_required()  # Attiva il controllo del token JWT se richiesto
def modify_profile():
    updated_data = request.form                     
    username = updated_data.get('username')
    field = updated_data.get('field')           # specify the text fields to be modified
    value = updated_data.get('value')           # for text fields

    # Controlla che il campo username sia fornito
    if not username:
        return jsonify({"error": "Missing required 'username' field"}), 400

    # Controlla che il campo non sia 'currency_balance'
    if field == 'currency_balance':
        return jsonify({"error": "Modifying 'currency_balance' field is not allowed"}), 400

    # Recupera il profilo da modificare
    profile = Profile.query.filter_by(username=username).first()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    # Controlla se l'utente ha inviato un'immagine
    if 'image' in request.files:
        file = request.files['image']

        # Verifica che l'immagine abbia un nome valido
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Verifica il tipo di file immagine
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400

        # Genera un nome sicuro per il file
        filename = secure_filename(file.filename)

        # Salva l'immagine nella cartella configurata
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        # Aggiorna il campo `profile_image` con il nuovo percorso
        profile.profile_image = save_path

    elif field:  # Modifica di altri campi
        # Controlla se il campo esiste nel modello Profile
        if not hasattr(profile, field):
            return jsonify({"error": f"Field '{field}' does not exist in profile"}), 400

        # Esegui la modifica del campo specificato
        setattr(profile, field, value)

    else:
        return jsonify({"error": "No valid field or image provided for update"}), 400

    # Salva le modifiche nel database
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Profile updated successfully", 
                    "profile": {
                        "username": profile.username,
                        "profile_image": f"http://localhost:5001/images_profile/uploads/{os.path.basename(profile.profile_image)}",
                        "currency_balance": profile.currency_balance
                    }}), 200

# Endpoint per visualizzare il profilo
@app.route('/checkprofile', methods=['GET'])
#@jwt_required()
def check_profile():
    username = request.args.get('username')
    profile = Profile.query.filter_by(username=username).first()
    
    if not profile:
        return jsonify({"error": "User not found"}), 401

    profile_data = {
        "username": profile.username,
        "profile_image": f"http://localhost:5001/images_profile/uploads/{os.path.basename(profile.profile_image)}",
        "currency_balance": profile.currency_balance,
    }
    return jsonify(profile_data), 200

# Endpoint per visualizzare la collezione gacha di un utente
@app.route('/retrieve_gachacollection', methods=['GET']) #--> Sistemare GACHA SYSTEM PER RICEVERE COLLEZIONI
#@jwt_required()
def retrieve_gacha_collection():
    username = request.args.get('username')
    profile = Profile.query.filter_by(username=username).first()
    
    if not profile:
        return jsonify({"error": "User not found"}), 401

    # Estrai la collezione di gachas dell'utente
    gacha_collection = [item.gacha_name for item in profile.gacha_collection]

    if not gacha_collection:
        return jsonify({"message": "User has no gachas"}), 200

    url="http://gachasystem:5004/get_gacha_collection" #AGGIUSTARE NUMERI PORTA
     # Se l'utente ha dei gachas nella collezione, li inviamo al servizio come parametro
    
        # Invia la lista di gacha_name come query string
        #response = requests.get(url, params={'gacha_name': ','.join(gacha_collection)}, timeout=10)
        # Invia la lista di gacha_name
    payload = {'gacha_name': ','.join(gacha_collection)}
    headers = {'Content-Type': 'application/json'}
    # response = requests.get(url, json=payload, headers=headers, timeout=10)
    res, status = profile_circuit_breaker.call('get', url , payload, headers, {}, True)
    if status != 200:
        return jsonify({'Error': 'Gacha service is down', 'details': res}), 500
    return res, 200
# Endpoint per visualizzare i dettagli di un oggetto gacha specifico
@app.route('/info_gachacollection', methods=['GET'])
#@jwt_required()
def info_gacha_collection():
    username = request.args.get('username')
    gacha_name = request.args.get('gacha_name')

    # Verifica che il profilo utente esista
    profile = Profile.query.filter_by(username=username).first()
    if not profile:
        return jsonify({"error": "User not found"}), 401

    # Costruisci i parametri per la richiesta
    params = {"gacha_name": gacha_name}
    url = "http://gachasystem:5004/get_gacha_collection"

        # Invia la richiesta al servizio Gacha
        # x = requests.get(url, json=params)
        # x.raise_for_status()  # Solleva un'eccezione per errori HTTP

        # # Decodifica i dati JSON restituiti dal servizio
        # response_data = x.json()
    res, status = profile_circuit_breaker.call('get', url, params, {},{}, True)
    if status == 200:
        return jsonify(res), 200
    return jsonify({"error": res}), 500


# route che serve le immagini
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Crea il percorso completo per la cartella "uploads"
    uploads_folder = os.path.join(app.root_path, 'static', 'uploads')
    
    # Restituisce il file dalla cartella "uploads", 404 se il file non esiste
    return send_from_directory(uploads_folder, filename)

# Funzione per controllare il tipo di file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/create_profile', methods=['POST'])
def create_profile():
    data = request.get_json()
    username = data.get('username')
    currency_balance = data.get('currency_balance', 0)

    if not username:
        return jsonify({"error": "Missing 'username' parameter"}), 400
    
    # Percorso immagine predefinita
    default_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'DefaultProfileIcon.jpg')

    # Percorso immagine salvata (valore predefinito)
    save_path = default_image_path
    
    if 'image' in request.files:
        file = request.files['image']

        # Verifica che l'immagine abbia un nome valido
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Verifica il tipo di file immagine
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400

        # Genera un nome sicuro per il file
        filename = secure_filename(file.filename)

        # Salva l'immagine nella cartella configurata
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

    try:
        # Controlla se il profilo esiste già
        existing_profile = Profile.query.filter_by(username=username).first()
        if existing_profile:
            return jsonify({"error": "Profile already exists"}), 400

        # Crea un nuovo profilo
        new_profile = Profile(
            username=username,
            profile_image=save_path,
            currency_balance=currency_balance
        )
        db.session.add(new_profile)
        db.session.commit()

        return jsonify({"message": f"Profile for username '{username}' created successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_profile', methods=['DELETE'])
def delete_profile():
    data= request.get_json()
    username = data.get('username')
    user = Profile.query.filter_by(username=username).first()
    if not user:
        return jsonify({'Error': 'User not found'}), 400
    db.session.delete(user)
    db.session.commit
    return jsonify({"message": f"Profile for username '{username}' deleted successfully"}), 200

@app.route('/insertGacha', methods=['POST'])
def insertGacha():
    # Recupera il JSON dalla richiesta
    data = request.get_json()

    # Controlla che i dati non siano nulli
    if not data:
        return jsonify({"error": "Missing request data"}), 400

    # Controlla che tutti i parametri obbligatori siano presenti
    username = data.get('username')
    gacha_name = data.get('gacha_name')
    collected_date_str = data.get('collected_date')

    if not username:
        return jsonify({"error": "Missing 'username' parameter"}), 400
    if not gacha_name:
        return jsonify({"error": "Missing 'gacha_name' parameter"}), 400
    if not collected_date_str:
        return jsonify({"error": "Missing 'collected_date' parameter"}), 400

    # Verifica che la data sia in un formato valido
    try:
        collected_date = datetime.fromisoformat(collected_date_str)
    except ValueError:
        return jsonify({"error": "Invalid 'collected_date' format. Use ISO format (e.g., 'YYYY-MM-DDTHH:MM:SS')"}), 400

    # Verifica che l'utente esista nel database
    profile = Profile.query.filter_by(username=username).first()
    if not profile:
        return jsonify({"error": f"User '{username}' not found"}), 404

    # Aggiungi il nuovo Gacha alla collezione
    try:
        newGacha = GachaItem(gacha_name=gacha_name, collected_date=collected_date, username=username)
        db.session.add(newGacha)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"An error occurred while adding Gacha: {str(e)}"}), 500

    return jsonify({"message": f"Gacha '{gacha_name}' added to collection for user '{username}'"}), 200


@app.route('/deleteGacha', methods=['DELETE'])
def deleteGacha():
    data = request.get_json()
    username = data.get('username')
    gacha_name = data.get('gacha_name')
    all = data.get('all', False)
    #collected_date = data.get('collected_date')

    if all:
        if not username or username == "null":
            # Elimina il GachaItem specificato per tutti gli utenti
            gacha_items = GachaItem.query.filter_by(gacha_name=gacha_name).all()
            if not gacha_items:
                return jsonify({"error": f"No Gacha items found with name {gacha_name}"}), 404
            
            for gacha in gacha_items:
                db.session.delete(gacha)
            db.session.commit()
            return jsonify({"message": f"Gacha items with name {gacha_name} have been deleted for all users"}), 200
    else:
        # Recupera l'utente
        profile = Profile.query.filter_by(username=username).first()
        if not profile:
            return jsonify({"error": "User not found"}), 400
        gacha = GachaItem.query.filter_by(
            gacha_name=gacha_name,
            username=profile.username
        ).first()
        if not gacha:
            return jsonify({"error": "Gacha not found"}), 404
        # Elimina il GachaItem
        db.session.delete(gacha)
        db.session.commit()
        return jsonify({"message": f"Gacha '{gacha_name}' deleted from collection"}), 200


if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5002)
