from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db:5432/auth_db'
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

# Endpoint per la creazione di un account
@app.route('/signup', methods=['POST'])
def signup():
    username = request.args.get('username')
    password = request.args.get('password')
    email = request.args.get('email')

    if not username or not password or not email:
        return jsonify({"error": "Missing parameters"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password, email=email)

    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Account created successfully"}), 200

# Endpoint per il login
@app.route('/login', methods=['POST'])
def login():
    username = request.args.get('username')
    password = request.args.get('password')

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity={'username': username})
        return jsonify(access_token=access_token), 200
    return jsonify({"error": "Invalid credentials"}), 404

# Endpoint per il logout (simulato, senza revoca token per semplicità)
@app.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    return jsonify({"message": "Logout success"}), 200

# Endpoint per l'eliminazione di un account
@app.route('/delete', methods=['DELETE'])
def delete_account():
    username = request.args.get('ID')
    password = request.args.get('password')

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Account deleted successfully"}), 200
    return jsonify({"error": "User not found or incorrect password"}), 404

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5001)
