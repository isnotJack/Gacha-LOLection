from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@auth_db:5432/auth_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

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
    try:
        x = requests.post(url, json=params, timeout=10)
        x.raise_for_status()
        res = x.json()
    except requests.exceptions.Timeout:
        return jsonify({"Error": "Time out expired"}), 408
    except requests.exceptions.RequestException as e:
        # Ritorna un errore se la chiamata al `profile_setting` fallisce
        return jsonify({'Error': f'Failed to create profile: {str(e)}'}), 500
    params = {
        'username': username,
    }
    url = 'http://payment_service:5006/newBalance'
    try:
        y = requests.post(url, json=params, timeout=10)
        y.raise_for_status()
        res = x.json()
    except requests.exceptions.Timeout:
        return jsonify({"Error": "Time out expired"}), 408
    except requests.exceptions.RequestException as e:
        # Ritorna un errore se la chiamata al `profile_setting` fallisce
        return jsonify({'Error': f'Failed to create profile: {str(e)}'}), 500 
    return jsonify({"msg": "Account created successfully", "profile_message": res.get("message")}), 200


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
        try:
            x = requests.delete(url, json=params, timeout=10)
            x.raise_for_status()
            res = x.json()
        except requests.exceptions.Timeout:
            return jsonify({"Error": "Time out expired"}), 408
        except requests.exceptions.RequestException as e:
            # Ritorna un errore se la chiamata al `profile_setting` fallisce
            return jsonify({'Error': f'Failed to delete profile: {str(e)}'}), 500
        url = 'http://payment_service:5006/deleteBalance'
        try:
            x = requests.delete(url, json=params, timeout=10)
            x.raise_for_status()
            res = x.json()
        except requests.exceptions.Timeout:
            return jsonify({"Error": "Time out expired"}), 408
        except requests.exceptions.RequestException as e:
            return jsonify({'Error': f'Failed to delete the balance: {str(e)}'}), 500
        return jsonify({"msg": "Account deleted successfully"}), 200
    else:
        return jsonify({"Error": "User not found or incorrect password"}), 404

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5001)
