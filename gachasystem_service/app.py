import os
import random
import requests, time
from flask import Flask, request, jsonify , url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
#from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import re

app = Flask(__name__)   # crea un'applicazione Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db_gachasystem:5432/memes_db'    # URL di connessione al database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False    # disabilita il tracciamento delle modifiche per migliorare le prestazioni
#app.config['JWT_SECRET_KEY'] = 'super-secret-key'

public_key_path = os.getenv("PUBLIC_KEY_PATH")

UPLOAD_FOLDER = '/app/static/uploads'  # Percorso dove Docker monta il volume
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Estensioni permesse
PROFILE_SETTING_URL = "https://profile_setting:5003/deleteGacha"  # Nome del container nel docker-compose

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
#bcrypt = Bcrypt(app)
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
                response = requests.request(method, url, json=params, headers=headers, verify=False)
            else:
                response = requests.request(method, url, data=params, headers=headers, files=files, verify=False)
            
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

# Funzione per sanitizzare stringhe generali
def sanitize_input(input_string):
    """Permette solo caratteri alfanumerici, trattini bassi, spazi e trattini."""
    if not input_string:
        return input_string
    return re.sub(r"[^\w\s-]", "", input_string)
def sanitize_input_gacha(input_string):
    """Permette solo caratteri alfanumerici, trattini bassi, spazi, trattini e punti."""
    if not input_string:
        return input_string
    return re.sub(r"[^\w\s\-.]", "", input_string)

# Modello Utente
# 
# La classe Gacha eredita da db.Model, che è la classe base fornita da SQLAlchemy
# La classe Gacha rappresenta la tabella SQL chiamata 'memes' 
# (i campi della tabella users vengono mappati agli attributi della classe python User)
class Gacha(db.Model):
    __tablename__ = 'memes'     # specifica il nome della tabella nel database
    gacha_id = db.Column(db.Integer, primary_key=True)
    meme_name = db.Column(db.String(50), unique=True, nullable=False)
    image_path = db.Column(db.String(200), nullable=False)  # Percorso dell'immagine
    rarity = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(100), nullable=True)
    #collected_date = db.Column(db.DateTime, default=func.now(), nullable=False)  # Data di raccolta

# Funzione per controllare il tipo di file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# SOLO ADMIN
@app.route('/add_gacha', methods=['POST'])
#@jwt_required() # Richiede un token JWT valido per accedere a questa funzione
def add_gacha():

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = jwt.decode(access_token, public_key, algorithms=["RS256"], audience="gachasystem")  
        if decoded_token.get("scope") == "user":
            return jsonify({"error": "Unauthorized action for the user"}), 403
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    

    name = sanitize_input_gacha(request.form.get('gacha_name'))
    rarity = sanitize_input(request.form.get('rarity'))
    description = sanitize_input(request.form.get('description'))

    # Controlla che tutti i campi siano forniti
    if not name or not rarity or 'image' not in request.files:
        return jsonify({"error": "Missing required fields (image, gacha_name, or rarity)"}), 400

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

    # Controlla se esiste già un record con lo stesso nome
    existing_gacha = Gacha.query.filter_by(meme_name=name).first()
    if existing_gacha:
        return jsonify({"error": f"A Gacha with the name '{name}' already exists."}), 400

    # Crea un nuovo oggetto Gacha
    new_gacha = Gacha(
        meme_name=name,
        image_path=save_path,  # Salva il percorso del file
        rarity=rarity,
        description=description
    )

    # Aggiungi al database e salva
    try:
        db.session.add(new_gacha)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Gacha added successfully", 
                    "gacha": {
                        "name": name,
                        "image_path": save_path,
                        "rarity": rarity,
                        "description": description
                        #,"collected_date": new_gacha.collected_date  # Restituisci anche la data di raccolta
                    }}), 200

@app.route('/delete_gacha', methods=['DELETE'])
# @jwt_required()  # Sblocca questa linea se vuoi proteggere l'endpoint con JWT
def delete_gacha():
    
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = jwt.decode(access_token, public_key, algorithms=["RS256"], audience="gachasystem")  
        if decoded_token.get("scope") == "user":
            return jsonify({"error": "Unauthorized action for the user"}), 403
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    # Recupera il nome del gacha dai parametri della query string
    data= request.get_json()
    gacha_name = sanitize_input_gacha(data.get('gacha_name'))
    if not gacha_name:
        return jsonify({"error": "Missing 'gacha_name' in query string."}), 400

    # Recupera il gacha dal database
    gacha = Gacha.query.filter_by(meme_name=gacha_name).first()

    # Verifica se il gacha esiste
    if not gacha:
        return jsonify({"error": f"Gacha with name '{gacha_name}' not found."}), 404

    # try:
        # Elimina l'immagine dal filesystem
    if gacha.image_path and os.path.exists(gacha.image_path):
        os.remove(gacha.image_path)
    
    # Rimuove il record dal database
    db.session.delete(gacha)
    db.session.commit()

    # Chiamata al servizio profile_setting per rimuovere il gacha
    payload = {
        "username": "null",
        "gacha_name": gacha_name,
        "all": True
    }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response,status = profile_circuit_breaker.call('delete', PROFILE_SETTING_URL, payload, headers, {}, True)
    # response = requests.delete(PROFILE_SETTING_URL, json=payload, timeout=10)
    # Verifica se la richiesta è andata a buon fine
    if status != 200 and status != 404:
        return jsonify({
            "error": "Gacha deleted locally, but failed to delete from user profiles.",
            "details": response.text
        }), status
# except Exception as e:
#     db.session.rollback()
#     return jsonify({"error": f"Failed to delete gacha: {str(e)}"}), 500

    return jsonify({"message": f"Gacha with name '{gacha_name}' deleted successfully."}), 200

@app.route('/update_gacha', methods=['PATCH'])
# @jwt_required()  # Sblocca questa linea se vuoi proteggere l'endpoint con JWT
def update_gacha():

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = jwt.decode(access_token, public_key, algorithms=["RS256"], audience="gachasystem")  
        if decoded_token.get("scope") == "user":
            return jsonify({"error": "Unauthorized action for the user"}), 403
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    # Estrai i parametri dalla query string
    data = request.get_json()
    name = sanitize_input_gacha(data.get('gacha_name'))
    rarity = sanitize_input(data.get('rarity'))
    description = sanitize_input(data.get('description'))

    # Verifica che il parametro 'name' sia presente
    if not name:
        return jsonify({"error": "Missing required field: 'name'"}), 400

    # Cerca il gacha con il nome fornito
    existing_gacha = Gacha.query.filter_by(meme_name=name).first()

    # Se non esiste, restituisce errore 404
    if not existing_gacha:
        return jsonify({"error": f"Gacha with name '{name}' not found."}), 404

    # Se 'rarity' è presente nella query string, aggiorna la rarità
    if rarity:
        existing_gacha.rarity = rarity

    # Se 'description' è presente nella query string, aggiorna la descrizione
    if description:
        existing_gacha.description = description

    # Commit delle modifiche al database
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    # Restituisci una risposta di successo con i dati aggiornati
    return jsonify({
        "message": "Gacha updated successfully",
        "gacha": {
            "name": existing_gacha.meme_name,
            "rarity": existing_gacha.rarity,
            "description": existing_gacha.description
        }
    }), 200

# route che serve le immagini
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Crea il percorso completo per la cartella "uploads"
    uploads_folder = os.path.join(app.root_path, 'static', 'uploads')
    # Restituisce il file dalla cartella "uploads", 404 se il file non esiste
    return send_from_directory(uploads_folder, filename)

@app.route('/get_gacha_collection', methods=['GET'])
def get_gacha_collection():
    
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        jwt.decode(access_token, public_key, algorithms=["RS256"], audience="gachasystem")  
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    data= request.get_json()
    # Estrai il parametro 'gacha_name' dalla query string (facoltativo), supporta una lista separata da virgola
    gacha_names = sanitize_input_gacha(data.get('gacha_name'))
    
    if gacha_names:
        # Suddividi i nomi in una lista
        # gacha_names = gacha_names.split(',')
        
        # Cerca i gachas con i nomi specificati
        gachas = Gacha.query.filter(Gacha.meme_name.in_(gacha_names)).all()
        
        if not gachas:
            return jsonify({"error": "No gachas found with the specified names"}), 404  # Se nessun gacha trovato con i nomi specificati
    else:
        # Se non viene passato 'gacha_name', restituiamo tutta la collezione di gachas
        gachas = Gacha.query.all()
        if not gachas:
            return jsonify({"error": "No gachas found"}), 404  # Se non ci sono gachas nella collezione
    
    # Dettagli della collezione di gachas
    gacha_list = []
    for gacha in gachas:
        gacha_details = {
            "gacha_id": gacha.gacha_id,
            "gacha_name": gacha.meme_name,
            "description": gacha.description or "",
            "rarity": gacha.rarity,
            #"collected_date": gacha.collected_date.isoformat(),  # Aggiungi la data di raccolta
            "img": f"https://localhost:5001/images_gacha/uploads/{os.path.basename(gacha.image_path)}"  # URL completo immagine
        }
        

        gacha_list.append(gacha_details)

    return jsonify(gacha_list), 200

@app.route('/get_gacha_roll', methods=['GET'])
def get_gacha_roll():

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        jwt.decode(access_token, public_key, algorithms=["RS256"], audience="gachasystem")  
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    # Estrai il parametro 'level' dalla query string
    level = sanitize_input(request.args.get('level'))
    
    # Definizione delle probabilità per ogni livello
    probabilities = {
        "standard": {"common": 70, "rare": 25, "legendary": 5},
        "medium": {"common": 50, "rare": 25, "legendary": 25},
        "premium": {"common": 30, "rare": 40, "legendary": 30},
    }

    # Controlla che il livello sia valido
    if level not in probabilities:
        return jsonify({"error": "Invalid level. Valid levels are 'standard', 'medium', and 'premium'."}), 400

    # Determina la rarità in base alle probabilità
    rarity_to_extract = random.choices(
        population=["common", "rare", "legendary"],
        weights=[
            probabilities[level]["common"],
            probabilities[level]["rare"],
            probabilities[level]["legendary"],
        ],
        k=1
    )[0]

    # Cerca casualmente un gacha dal database in base alla rarità
    gacha = Gacha.query.filter_by(rarity=rarity_to_extract).order_by(func.random()).first()

    # Controlla se un gacha è stato trovato
    if not gacha:
        return jsonify({"error": f"No gacha found for a roll of level '{level}'."}), 404

    # Prepara i dettagli del gacha per la risposta
    gacha_details = {
        "gacha_id": gacha.gacha_id,
        "gacha_name": gacha.meme_name,
        "description": gacha.description or "",
        "rarity": gacha.rarity,
        #"collected_date": gacha.collected_date.isoformat(),
        "img": f"https://localhost:5001/images_gacha/uploads/{os.path.basename(gacha.image_path)}"
    }

    return jsonify(gacha_details), 200


if __name__ == '__main__':
    db.create_all()
   # app.run(host='0.0.0.0', port=5004)