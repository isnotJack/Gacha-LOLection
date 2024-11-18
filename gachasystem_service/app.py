import os
import random
import requests
from flask import Flask, request, jsonify , url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
#from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

app = Flask(__name__)   # crea un'applicazione Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db_gachasystem:5432/memes_db'    # URL di connessione al database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False    # disabilita il tracciamento delle modifiche per migliorare le prestazioni
#app.config['JWT_SECRET_KEY'] = 'super-secret-key'

UPLOAD_FOLDER = '/app/static/uploads'  # Percorso dove Docker monta il volume
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Estensioni permesse
PROFILE_SETTING_URL = "http://profile_setting:5003/deleteGacha"  # Nome del container nel docker-compose

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
#bcrypt = Bcrypt(app)
jwt = JWTManager(app)

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

@app.route('/add_gacha', methods=['POST'])
#@jwt_required() # Richiede un token JWT valido per accedere a questa funzione
def add_gacha():

    #current_user = get_jwt_identity()
    #username = current_user['username']
    #role = current_user['role']
    # Controlla che l'utente abbia il ruolo di 'admin'
    #if role != 'admin':
    #    return jsonify({"error": "You are not authorized to perform this action"}), 403 # forbidden

    name = request.form.get('gacha_name')
    rarity = request.form.get('rarity')
    description = request.form.get('description')

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
    
    #current_user = get_jwt_identity()
    #username = current_user['username']
    #role = current_user['role']
    # Controlla che l'utente abbia il ruolo di 'admin'
    #if role != 'admin':
    #    return jsonify({"error": "You are not authorized to perform this action"}), 403 # forbidden

    # Recupera il nome del gacha dai parametri della query string
    data= request.get_json()
    gacha_name = data.get('gacha_name')
    if not gacha_name:
        return jsonify({"error": "Missing 'gacha_name' in query string."}), 400

    # Recupera il gacha dal database
    gacha = Gacha.query.filter_by(meme_name=gacha_name).first()

    # Verifica se il gacha esiste
    if not gacha:
        return jsonify({"error": f"Gacha with name '{gacha_name}' not found."}), 404

    try:
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
        response = requests.delete(PROFILE_SETTING_URL, json=payload)
        # Verifica se la richiesta è andata a buon fine
        if response.status_code != 200:
            return jsonify({
                "error": "Gacha deleted locally, but failed to delete from user profiles.",
                "details": response.text
            }), response.status_code

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete gacha: {str(e)}"}), 500

    return jsonify({"message": f"Gacha with name '{gacha_name}' deleted successfully."}), 200

@app.route('/update_gacha', methods=['PATCH'])
# @jwt_required()  # Sblocca questa linea se vuoi proteggere l'endpoint con JWT
def update_gacha():

    #current_user = get_jwt_identity()
    #username = current_user['username']
    #role = current_user['role']
    # Controlla che l'utente abbia il ruolo di 'admin'
    #if role != 'admin':
    #    return jsonify({"error": "You are not authorized to perform this action"}), 403 # forbidden

    # Estrai i parametri dalla query string
    data = request.get_json()
    name = data.get('gacha_name')
    rarity = data.get('rarity')
    description = data.get('description')

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
    
    data= request.get_json()
    # Estrai il parametro 'gacha_name' dalla query string (facoltativo), supporta una lista separata da virgola
    gacha_names = data.get('gacha_name')
    
    if gacha_names:
        # Suddividi i nomi in una lista
        gacha_names = gacha_names.split(',')
        
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
            "img": f"http://localhost:5001/images_gacha/uploads/{os.path.basename(gacha.image_path)}"  # URL completo immagine
        }
        

        gacha_list.append(gacha_details)

    return jsonify(gacha_list), 200


@app.route('/get_gacha_roll', methods=['GET'])
def get_gacha_roll():
    # Estrai il parametro 'level' dalla query string
    level = request.args.get('level')
    
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
        "img": f"http://localhost:5001/images_gacha/uploads/{os.path.basename(gacha.image_path)}"
    }

    return jsonify(gacha_details), 200


if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5004)