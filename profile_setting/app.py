from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import requests
from requests.exceptions import ConnectionError, HTTPError
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@profile_db:5432/profile_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

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
        return jsonify({"error": "User has no gachas"}), 404

    url="http://gachasystem:5004/get_gacha_collection" #AGGIUSTARE NUMERI PORTA
     # Se l'utente ha dei gachas nella collezione, li inviamo al servizio come parametro
    try:
        # Invia la lista di gacha_name come query string
        response = requests.get(url, params={'gacha_name': ','.join(gacha_collection)})

        # Verifica se la risposta è andata a buon fine
        response.raise_for_status()

        # Estrai i dati dal servizio e restituisci la risposta
        response_data = response.json()
        return jsonify(response_data), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'Error': 'Gacha service is down', 'details': str(e)}), 500

# Endpoint per visualizzare i dettagli di un oggetto gacha specifico
@app.route('/info_gachacollection', methods=['GET'])
@jwt_required()
def info_gacha_collection():
    username = request.args.get('username')
    gacha_name = request.args.get('gacha_name')
    profile = Profile.query.filter_by(username=username).first()

    if not profile:
        return jsonify({"error": "User not found"}), 401

    gacha ={
        "gacha_name": gacha_name
        }

    url="http://gatchasystem_service:5005/get_gacha_collection" #AGGIUSTARE NUMERI PORTA
    try:
        x=requests.get(url,gacha)
        x.raise_for_status()
        response_data = x.json()
        return jsonify(response_data), 200
    except ConnectionError:
            return jsonify({'Error':'Gacha service is down'}),404
    except HTTPError:
            return jsonify(x.content, x.status_code)

@app.route('/create_profile', methods=['POST'])
def create_profile():
    data = request.get_json()
    username = data.get('username')
    profile_image = data.get('profile_image', 'default_image_url')
    currency_balance = data.get('currency_balance', 0)

    if not username:
        return jsonify({"error": "Missing 'username' parameter"}), 400

    try:
        # Controlla se il profilo esiste già
        existing_profile = Profile.query.filter_by(username=username).first()
        if existing_profile:
            return jsonify({"error": "Profile already exists"}), 400

        # Crea un nuovo profilo
        new_profile = Profile(
            username=username,
            profile_image=profile_image,
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
    data = request.get_json()
    username = data.get('username')
    gacha_name=data.get('gacha_name')
    collected_date_str=data.get('collected_date')
    collected_date = datetime.fromisoformat(collected_date_str)
    newGacha = GachaItem(gacha_name=gacha_name, collected_date=collected_date, username=username)
    db.session.add(newGacha)
    db.session.commit()
    return jsonify({"message": f"Gacha '{gacha_name}' added to collection"}), 200

@app.route('/deleteGacha', methods=['DELETE'])
def deleteGacha():
    data = request.get_json()
    username = data.get('username')
    gacha_name = data.get('gacha_name')
    collected_date = data.get('collected_date')

    # Recupera l'utente
    profile = Profile.query.filter_by(username=username).first()
    if not profile:
        return jsonify({"error": "User not found"}), 400

    # Trova il GachaItem corrispondente
    gacha = GachaItem.query.filter_by(
        gacha_name=gacha_name,
        collected_date=collected_date,
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
