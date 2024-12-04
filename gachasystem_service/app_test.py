import os
import random
from datetime import datetime
from flask import Flask, request, jsonify , url_for, send_from_directory
from werkzeug.utils import secure_filename
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import re

app = Flask(__name__)   # crea un'applicazione Flask


public_key_path = os.getenv("PUBLIC_KEY_PATH")

UPLOAD_FOLDER = '/app/static/uploads'  # Percorso dove Docker monta il volume
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Estensioni permesse

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Funzione per sanitizzare stringhe generali
def sanitize_input(input_string):
    """Permette solo caratteri alfanumerici, trattini bassi, spazi e trattini."""
    if not input_string:
        return input_string
    return re.sub(r"[^\w\s-]", "", input_string)
def sanitize_input_gacha(input_value):
    """Sanitizza l'input per permettere solo caratteri alfanumerici, trattini bassi, spazi, trattini e punti."""
    if isinstance(input_value, str):
        return re.sub(r"[^\w\s\-.]", "", input_value)
    elif isinstance(input_value, list):
        return [sanitize_input_gacha(item) for item in input_value if isinstance(item, str)]
    elif isinstance(input_value, (int, float)):
        return str(input_value)
    else:
        return ""

# Funzione per controllare il tipo di file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def mock_decode_jwt(token, public_key, algorithms, audience):
    # Simula una risposta di decodifica valida
    if token == "valid_token":
        return {
            "sub": "admin1",
            "aud": audience,
            "exp": int(datetime.now().timestamp()) + 3600,  # Token valido per un'ora
            "scope" : "admin"
        }
    elif token == "valid_token1":
        return {
            "sub": "user1",
            "aud": audience,
            "exp": int(datetime.now().timestamp()) + 3600,  # Token valido per un'ora
            "scope" : "user"
        }
    elif token == "expired_token":
        raise jwt.ExpiredSignatureError("Token expired")
    else:
        raise jwt.InvalidTokenError("Invalid token")

def mock_search_gacha(name):
    if name == 'existed':
        return {
            'meme_name' : 'Trial',
            'rarity' : 'common',
            'descriptio': 'A common gacha'
        }
    return False

def mock_insert_gacha(meme_name,image_path,rarity,description):
    return jsonify({'msg':'gacha correctly inserted'})
@app.route('/add_gacha', methods=['POST'])
def add_gacha():

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="gachasystem")  
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


    existing_gacha = mock_search_gacha(name)
    if existing_gacha:
        return jsonify({"error": f"A Gacha with the name '{name}' already exists."}), 400


    mock_insert_gacha( meme_name=name,
        image_path=save_path,  
        rarity=rarity,
        description=description)

    return jsonify({"message": "Gacha added successfully", 
                    "gacha": {
                        "name": name,
                        "image_path": save_path,
                        "rarity": rarity,
                        "description": description
                    }}), 200
def mock_profile(payload):
    return jsonify({"message": f"Gacha '{payload['gacha_name']}' deleted from collection"}), 200

@app.route('/delete_gacha', methods=['DELETE'])
def delete_gacha():
    
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="gachasystem")  
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
    gacha = mock_search_gacha(gacha_name)
    # Verifica se il gacha esiste
    if not gacha:
        return jsonify({"error": f"Gacha with name '{gacha_name}' not found."}), 404

    # try:
        # Elimina l'immagine dal filesystem
    # if gacha.image_path and os.path.exists(gacha.image_path):
    #     os.remove(gacha.image_path)
    
    

    # Chiamata al servizio profile_setting per rimuovere il gacha
    payload = {
        "username": "null",
        "gacha_name": gacha_name,
        "all": True
    }
    response,status = mock_profile(payload)

    if status != 200 and status != 404:
        return jsonify({
            "error": "Gacha deleted locally, but failed to delete from user profiles.",
            "details": response.text
        }), status


    return jsonify({"message": f"Gacha with name '{gacha_name}' deleted successfully."}), 200

@app.route('/update_gacha', methods=['PATCH'])
def update_gacha():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401
    access_token = auth_header.removeprefix("Bearer ").strip()

    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="gachasystem")  
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
    existing_gacha = mock_search_gacha(name)

    # Se non esiste, restituisce errore 404
    if not existing_gacha:
        return jsonify({"error": f"Gacha with name '{name}' not found."}), 404

    # Se 'rarity' è presente nella query string, aggiorna la rarità
    if rarity:
        existing_gacha['rarity'] = rarity

    # Se 'description' è presente nella query string, aggiorna la descrizione
    if description:
        existing_gacha['description'] = description

    # Commit delle modifiche al database
    

    # Restituisci una risposta di successo con i dati aggiornati
    return jsonify({
        "message": "Gacha updated successfully",
        "gacha": {
            "name": existing_gacha['meme_name'],
            "rarity": existing_gacha['rarity'],
            "description": existing_gacha['description']
        }
    }), 200

# route che serve le immagini
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Crea il percorso completo per la cartella "uploads"
    uploads_folder = os.path.join(app.root_path, 'static', 'uploads')
    # Restituisce il file dalla cartella "uploads", 404 se il file non esiste
    return send_from_directory(uploads_folder, filename)

mock_gacha_db = [
    {
        "gacha_id": 1,
        "meme_name": "Rare Gacha 1",
        "description": "A rare collectible gacha",
        "rarity": "rare",
        "image_path": "/mock_images/gacha1.png"
    },
    {
        "gacha_id": 2,
        "meme_name": "Common Gacha 2",
        "description": "A common gacha for beginners",
        "rarity": "common",
        "image_path": "/mock_images/gacha2.png"
    },
    {
        "gacha_id": 3,
        "meme_name": "Legendary Gacha 3",
        "description": "An extremely rare legendary gacha",
        "rarity": "legendary",
        "image_path": "/mock_images/gacha3.png"
    },
    {
        "gacha_id": 4,
        "meme_name": "Legendary Gacha 4",
        "description": "A mythical gacha, rare beyond belief",
        "rarity": "legendary",
        "image_path": "/mock_images/gacha4.png"
    },
    {
        "gacha_id": 5,
        "meme_name": "Rare Gacha 5",
        "description": "Another rare gacha to collect",
        "rarity": "rare",
        "image_path": "/mock_images/gacha5.png"
    },
    {
        "gacha_id": 6,
        "meme_name": "Common Gacha 6",
        "description": "A common gacha for casual players",
        "rarity": "common",
        "image_path": "/mock_images/gacha6.png"
    },
    {
        "gacha_id": 7,
        "meme_name": "Legendary Gacha 7",
        "description": "A legendary gacha infused with mystery",
        "rarity": "legendary",
        "image_path": "/mock_images/gacha7.png"
    }
]

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
        mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="gachasystem")  
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    data= request.get_json()
    # Estrai il parametro 'gacha_name' dalla query string (facoltativo), supporta una lista separata da virgola
    # gacha_names = sanitize_input_gacha(data.get('gacha_name'))
    gacha_names = data.get('gacha_name')

    # Sanitizza e verifica l'input
    if gacha_names:
        gacha_names = sanitize_input_gacha(gacha_names)

        if isinstance(gacha_names, list):
            gachas = [g for g in mock_gacha_db if g["meme_name"] in gacha_names]
        elif isinstance(gacha_names, str):
            gachas = [g for g in mock_gacha_db if g["meme_name"] == gacha_names]
        else:
            return jsonify({"error": "Invalid input for gacha_name"}), 400

        if not gachas:
            return jsonify({"error": "No gachas found with the specified names"}), 404
    else:
        # Restituisci tutta la collezione di gacha mockati
        gachas = mock_gacha_db

    
    # Dettagli della collezione di gachas
    gacha_list = []
    for gacha in gachas:
        gacha_details = {
            "gacha_id": gacha['gacha_id'],
            "gacha_name": gacha['meme_name'],
            "description": "",
            "rarity": gacha['rarity'],
            "img": f"https://localhost:5001/images_gacha/uploads/"  # URL completo immagine
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
       mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="gachasystem")  
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


    filtered_gachas = [g for g in mock_gacha_db if g["rarity"] == rarity_to_extract]
    if not filtered_gachas:
        return jsonify({"error": f"No gacha found for a roll of level '{level}'."}), 404

    # Scegli un gacha casuale dalla lista filtrata
    gacha = random.choice(filtered_gachas)

    # Prepara i dettagli del gacha per la risposta
    gacha_details = {
        "gacha_id": gacha['gacha_id'],
        "gacha_name": gacha['meme_name'],
        "description": "",
        "rarity": gacha['rarity'],
        "img": f"https://localhost:5001/images_gacha/uploads/"
    }

    return jsonify(gacha_details), 200

