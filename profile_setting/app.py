from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db:5432/profile_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Modello per il profilo utente
class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    profile_image = db.Column(db.String(200), nullable=True)
    currency_balance = db.Column(db.Integer, default=0)
    gacha_collection = db.relationship('GachaItem', backref='profile', lazy=True)

# Modello per gli oggetti gacha
class GachaItem(db.Model):
    __tablename__ = 'gacha_items'
    id = db.Column(db.Integer, primary_key=True)
    gacha_id = db.Column(db.String(50), nullable=False)
    gacha_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    rarity = db.Column(db.String(50), nullable=True)
    collected_date = db.Column(db.String(50), nullable=True)
    img = db.Column(db.String(255), nullable=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)

# Endpoint per modificare il profilo
@app.route('/modify', methods=['PATCH'])
#@jwt_required()
def modify_profile():
    updated_data= request.get_json()
    username = updated_data.get('username')
    field = updated_data.get('field')
    value = updated_data.get('value')
    #current_user = get_jwt_identity()

    # Controllo se l'utente è autorizzato a modificare il profilo
    #if current_user != username:
    #    return jsonify({"error": "Unauthorized to modify this profile"}), 401

    # Recupera il profilo da modificare
    profile = Profile.query.filter_by(username=username).first()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    # Controlla se il campo specificato esiste nel modello Profile
    if not hasattr(profile, field):
        return jsonify({"error": f"Field '{field}' does not exist in profile"}), 400

    # Esegui la modifica del campo specificato
    setattr(profile, field, value)
    db.session.commit()
    
    return jsonify({"message": f"Profile field '{field}' updated successfully"}), 200


# Endpoint per visualizzare il profilo
@app.route('/checkprofile', methods=['GET'])
@jwt_required()
def check_profile():
    username = request.args.get('username')
    profile = Profile.query.filter_by(username=username).first()
    
    if not profile:
        return jsonify({"error": "User not found"}), 401

    profile_data = {
        "username": profile.username,
        "profile_image": profile.profile_image,
        "currency_balance": profile.currency_balance,
    }
    return jsonify(profile_data), 200

# Endpoint per visualizzare la collezione gacha di un utente
@app.route('/retrieve_gachacollection', methods=['GET'])
@jwt_required()
def retrieve_gacha_collection():
    username = request.args.get('username')
    profile = Profile.query.filter_by(username=username).first()
    
    if not profile:
        return jsonify({"error": "User not found"}), 401

    gacha_collection = [{
        "gacha_id": item.gacha_id,
        "gacha_name": item.gacha_name,
        "description": item.description,
        "rarity": item.rarity,
        "collected_date": item.collected_date,
        "img": item.img
    } for item in profile.gacha_collection]

    response_data = {
        "username": username,
        "gacha_collected": gacha_collection,
        "total_gacha": len(gacha_collection),
        "remaining_to_complete": 100 - len(gacha_collection)  # DA MODIFICARE: Supponendo che la collezione completa sia di 100 elementi
    }
    return jsonify(response_data), 200

# Endpoint per visualizzare i dettagli di un oggetto gacha specifico
@app.route('/info_gachacollection', methods=['GET'])
@jwt_required()
def info_gacha_collection():
    username = request.args.get('username')
    gacha_id = request.args.get('gacha_id')
    profile = Profile.query.filter_by(username=username).first()

    if not profile:
        return jsonify({"error": "User not found"}), 401

    gacha_item = GachaItem.query.filter_by(profile_id=profile.id, gacha_id=gacha_id).first()
    if not gacha_item:
        return jsonify({"error": "Gacha item not found"}), 404

    gacha_data = {
        "gacha_id": gacha_item.gacha_id,
        "gacha_name": gacha_item.gacha_name,
        "description": gacha_item.description,
        "rarity": gacha_item.rarity,
        "collected_date": gacha_item.collected_date,
        "img": gacha_item.img
    }
    return jsonify(gacha_data), 200

# Endpoint per creare un nuovo profilo
@app.route('/create_profile', methods=['POST'])
def create_profile():
# Recupera i dati inviati nella richiesta
    data=request.get_json()
    username = data.get('username')
    profile_image =  'default_image_url'  # Immagine di profilo predefinita
    currency_balance = 0  # Bilancio predefinito

    # Controlla se il profilo esiste già
    if Profile.query.filter_by(username=username).first():
        return jsonify({"error": "Profile already exists"}), 400

    # Crea un nuovo profilo
    new_profile = Profile(
        username=username,
        profile_image=profile_image,
        currency_balance=currency_balance
    )
    db.session.add(new_profile)
    db.session.commit()

    return jsonify({"message": f"Profile for username '{username}' created successfully"}),200

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5002)
