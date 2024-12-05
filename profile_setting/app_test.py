from flask import Flask, request, jsonify, send_from_directory
import requests
import os, time
from datetime import datetime
from werkzeug.utils import secure_filename
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import re 

app = Flask(__name__)

public_key_path = os.getenv("PUBLIC_KEY_PATH")

UPLOAD_FOLDER = '/app/static/uploads'  # Percorso dove Docker monta il volume
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}  # Estensioni permesse

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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
            "sub": "user5",
            "aud": audience,
            "exp": int(datetime.now().timestamp()) + 3600,  # Token valido per un'ora
            "scope": "user"
        }
    if token == "valid_token3":
        return {
            "sub": "admin1",
            "aud": audience,
            "exp": int(datetime.now().timestamp()) + 3600,  # Token valido per un'ora
            "scope" : "admin"
        }
    elif token == "expired_token":
        raise jwt.ExpiredSignatureError("Token expired")
    else:
        raise jwt.InvalidTokenError("Invalid token")

# Generale: sanitizza stringhe generiche (es. username, campi testo)
def sanitize_input(input_string):
    """Permette solo caratteri alfanumerici, spazi, trattini e underscore."""
    if not input_string:
        return input_string
    return re.sub(r"[^\w\s-]", "", input_string)

# Specifico: include punti per email o nomi di file
def sanitize_email(input_string):
    """Permette solo caratteri validi per un'email."""
    if not input_string:
        return input_string
    return re.sub(r"[^\w\.\@\s-]", "", input_string)

def sanitize_input_gacha(input_string):
    """Permette solo caratteri alfanumerici, trattini bassi, spazi, trattini e punti."""
    if not input_string:
        return input_string
    return re.sub(r"[^\w\s\-.]", "", input_string)

def mock_find_profile(username):
    if username== 'user5':
        return False
    else:
        return {
                "username": 'user1',
                "email": 'user1@gmail.com',
                "profile_image": f"https://localhost:5001/images_profile/uploads",
                "currency_balance": 100,
                "gacha_collection" : [
                        {"gacha_name" : "Trial gacha 1"}, 
                        {"gacha_name" : "Tria gacha 2"}]
        }
# Endpoint per modificare il profilo
@app.route('/modify_profile', methods=['PATCH'])
def modify_profile():
    updated_data = request.form
    username = sanitize_input(updated_data.get('username'))

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="profile_setting")  
        if username and decoded_token.get("sub") != username:
            return jsonify({"error": "Username in token does not match the request username"}), 403
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    field = sanitize_input(updated_data.get('field'))           # specify the text fields to be modified
    value = sanitize_input(updated_data.get('value'))           # for text fields

    # Controlla che il campo username sia fornito
    if not username:
        return jsonify({"error": "Missing required 'username' field"}), 400
    
    # Controlla che il campo non sia 'currency_balance'
    if field == 'currency_balance':
        return jsonify({"error": "Modifying 'currency_balance' field is not allowed"}), 400

    # Recupera il profilo da modificare
    profile = mock_find_profile(username)
    # controllo forse inutile
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
        profile['profile_image'] = save_path

    if field:  # Modifica di altri campi
        # Controlla se il campo esiste nel modello Profile
        if not hasattr(profile, field):
            return jsonify({"error": f"Field '{field}' does not exist in profile"}), 400

        # Esegui la modifica del campo specificato
        setattr(profile, field, value)

    if 'image' not in request.files and not field:
        return jsonify({"error": "No valid field or image provided for update"}), 400

    # Salva le modifiche nel database
   

    return jsonify({"message": "Profile updated successfully", 
                    "profile": {
                        "username": profile['username'],
                        "email": profile['email'],
                        "profile_image": f"https://localhost:5001/images_profile/uploads/{os.path.basename(profile['profile_image'])}",
                        "currency_balance": profile['currency_balance']
                    }}), 200

def mock_getBalance(username):
    if username == 'not_found':
        return {}
    else: 
        return {
            "username" : username,
            "balance" : 100
        }
    
# Endpoint per visualizzare il profilo
@app.route('/checkprofile', methods=['GET'])
def check_profile():
    username = sanitize_input(request.args.get('username'))
    if not username:
        return jsonify({"error": "Missing Parameters"}), 400
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="profile_setting")  
        if username and decoded_token.get("sub") != username:
            return jsonify({"error": "Username in token does not match the request username"}), 403
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    
    profile = mock_find_profile(username)
    # controllo forse inutile
    if not profile:
        return jsonify({"error": "User not found"}), 401

    res, status = mock_getBalance(username)
    if status != 200:
        balance = profile['currency_balance']
    else:
        balance = res['balance']
        profile['currency_balance'] = balance
    
    profile_data = {
        "username": profile['username'],
        "email": profile['email'],
        "profile_image": f"https://localhost:5001/images_profile/uploads/{profile['profile_image']}",
        "currency_balance": balance,
    }
    return jsonify(profile_data), 200
def mock_get_gacha_coll(gacha_names):
   
    # Estraggo i nomi dalla lista
    gacha = gacha_names['gacha_name']
    if not gacha:
        return "No gacha names provided", 200
    if 'no_gacha' in gacha:
        return {'Error': 'No gacha found'}, 404
    # Restituisco tutti i gacha
    return gacha, 200

# Endpoint per visualizzare la collezione gacha di un utente
@app.route('/retrieve_gachacollection', methods=['GET']) #--> Sistemare GACHA SYSTEM PER RICEVERE COLLEZIONI
def retrieve_gacha_collection():
    username = sanitize_input(request.args.get('username'))
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="profile_setting")  
        if username and decoded_token.get("sub") != username:
            return jsonify({"error": "Username in token does not match the request username"}), 403
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    profile = mock_find_profile(username)
    
    if not profile:
        return jsonify({"error": "User not found"}), 401

    # Estrai la collezione di gachas dell'utente
    gacha_collection = [item['gacha_name'] for item in profile['gacha_collection']]

    if not gacha_collection:
        return jsonify({"message": "User has no gachas"}), 200

    payload = {'gacha_name': gacha_collection}
    res, status = mock_get_gacha_coll(payload)
    if status != 200:
        return jsonify({'Error': 'Gacha service is down', 'details': res}), 500
    return jsonify(res), 200
 
# Endpoint per visualizzare i dettagli di un oggetto gacha specifico
@app.route('/info_gachacollection', methods=['GET'])
def info_gacha_collection():
    username = sanitize_input(request.args.get('username'))

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="profile_setting")  
        if username and decoded_token.get("sub") != username:
            return jsonify({"error": "Username in token does not match the request username"}), 403
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    gacha_name = request.args.get('gacha_name')
    if gacha_name and gacha_name != "None":
        # Dividi i nomi separati da virgole (opzionale se supporti più valori separati)
        gacha_names = [name.strip() for name in gacha_name.split(',')]
    else:
        gacha_names = []  # Lista vuota se `gacha_name` non è presente

    # Verifica che il profilo utente esista
    profile = mock_find_profile(username)
    if not profile:
        return jsonify({"error": "User not found"}), 401

    # Costruisci i parametri per la richiesta
    params = {"gacha_name": gacha_names}
    
    res, status =  mock_get_gacha_coll(params)
    if status == 200:
        return jsonify(res), 200
    return jsonify({"error": res}), status


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

def mock_newProfile(username,email,profile_image,currency_balance):
    return {
        'username' : username,
        'email' : email,
        'profile_img' : profile_image,
        'currency_balance':currency_balance
    }

@app.route('/create_profile', methods=['POST'])
def create_profile():
    data = request.get_json()
    username = sanitize_input(data.get('username'))
    email = sanitize_email(data.get('email'))
    currency_balance = data.get('currency_balance', 0)

    if not username:
        return jsonify({"error": "Missing 'username' parameter"}), 400
    
    if not email:
        return jsonify({"error": "Missing 'email' parameter"}), 400 
    
    if not isinstance(currency_balance, (int, float)):
        return jsonify({"error": "currency_balance must be int or float"}), 400
    
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
        existing_profile = mock_find_profile(username)
        if existing_profile:
            return jsonify({"error": "Profile already exists"}), 500

        # Crea un nuovo profilo
        new_profile = mock_newProfile(
            username=username,
            email=email,
            profile_image=save_path,
            currency_balance=currency_balance
        )

        return jsonify({"message": f"Profile for username '{username}' created successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
def mock_delete(user):
    return "User succesfully deleted"
@app.route('/delete_profile', methods=['DELETE'])
def delete_profile():
    data= request.get_json()
    username = sanitize_input(data.get('username'))
    if not username:
        return jsonify({"error": "Missing parameters"}), 400
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="profile_setting")  
        if username and decoded_token.get("sub") != username:
            return jsonify({"error": "Username in token does not match the request username"}), 403
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    user =mock_find_profile(username)
    if not user:
        return jsonify({'Error': 'User not found'}), 404
    mock_delete(user)
    return jsonify({"message": f"Profile for username '{username}' deleted successfully"}), 200

def mock_newGacha(gacha_name, collected_date, username):
    return {
        'gacha_name': gacha_name,
        'collected_date': collected_date,
        'username' : username
    }
@app.route('/insertGacha', methods=['POST'])
def insertGacha():
    # Recupera il JSON dalla richiesta
    data = request.get_json()
    # Controlla che i dati non siano nulli
    if not data:
        return jsonify({"error": "Missing request data"}), 400

    username = sanitize_input(data.get('username'))  
    gacha_name = sanitize_input_gacha(data.get('gacha_name'))
    collected_date_str = data.get('collected_date')
    # Controlla che tutti i parametri obbligatori siano presenti
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
    profile = mock_find_profile(username)
    if not profile:
        return jsonify({"error": f"User '{username}' not found"}), 404

    # Aggiungi il nuovo Gacha alla collezione
    try:
        newGacha = mock_newGacha(gacha_name=gacha_name, collected_date=collected_date, username=username)
    except Exception as e:
        return jsonify({"error": f"An error occurred while adding Gacha: {str(e)}"}), 500

    return jsonify({"message": f"Gacha '{gacha_name}' added to collection for user '{username}'"}), 200

def mock_find_gacha(gacha_name=None, username=None):
    if gacha_name and gacha_name=='no_gacha':
        return False
    return [{
        'gacha_name': 'Trial gacha 1',
        'date' : '12/12/12'},
        {'gacha_name': 'Trial gacha 2',
        'date' : '12/12/12'}
        ]
def mock_delete_gacha(gacha):
    return "Gacha deleted"
@app.route('/deleteGacha', methods=['DELETE'])
def deleteGacha():
    data = request.get_json()
    username = sanitize_input(data.get('username'))

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="profile_setting")  
        if username and username != "null" and decoded_token.get("sub") != username:
            return jsonify({"error": "Username in token does not match the request username"}), 403
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    gacha_name = data.get('gacha_name')
    all = data.get('all', False)
    #collected_date = data.get('collected_date')

    if all:
        if not username or username == "null":
            # Elimina il GachaItem specificato per tutti gli utenti
            gacha_items = mock_find_gacha(gacha_name)
            if not gacha_items:
                return jsonify({"error": f"No Gacha items found with name {gacha_name}"}), 404
            
            for gacha in gacha_items:
                mock_delete_gacha(gacha)
            return jsonify({"message": f"Gacha items with name {gacha_name} have been deleted for all users"}), 200
    else:
        # Recupera l'utente
        profile = mock_find_profile(username)
        if not profile:
            return jsonify({"error": "User not found"}), 400
        gacha = mock_find_gacha(gacha_name,username)
        if not gacha:
            return jsonify({"error": "Gacha not found"}), 404
        # Elimina il GachaItem
        mock_delete_gacha(gacha)
        return jsonify({"message": f"Gacha '{gacha_name}' deleted from collection"}), 200


