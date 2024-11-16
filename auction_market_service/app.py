import os
from flask import Flask, request, jsonify , url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
#from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@auction_db:5432/auction_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Modello Auction
class Auction(db.Model):
    __tablename__ = 'auctions'
    id = db.Column(db.Integer, primary_key=True)
    gatcha_id = db.Column(db.Integer, nullable=False)
    seller_id = db.Column(db.Integer, nullable=False)
    winner_id = db.Column(db.Integer)
    current_bid = db.Column(db.Float, default=0.0)
    base_price = db.Column(db.Float, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(10), default='active')

    def to_dict(self):
        return {
            "id": self.id,
            "gatcha_id": self.gatcha_id,
            "seller_id": self.seller_id,
            "winner_id": self.winner_id,
            "current_bid": self.current_bid,
            "base_price": self.base_price,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status
        }


@app.route('/see', methods=['GET'])
def see_auctions():
    auction_id = request.args.get('auction_id')
    status = request.args.get('status', 'active')

    if auction_id:
        auction = Auction.query.get(auction_id)
        if auction:
            return jsonify(auction.to_dict()), 200
        else:
            return jsonify({"error": "Auction not found"}), 404
    #se il valore di auction id non è fornito allora ritorna tutte le aste attive
    auctions = Auction.query.filter_by(status=status).all()
    return jsonify([auction.to_dict() for auction in auctions]), 200


@app.route('/create', methods=['POST'])
#@jwt_required()
def create_auction():
        # Recupera l'identità dell'utente dal JWT, senza controllo del ruolo
 #   current_user = get_jwt_identity()
    # Legge i dati dalla richiesta JSON
    data = request.get_json()
    
    # Recupera i parametri dall'oggetto JSON
    seller_id = data.get('seller_id')
    gatcha_id = data.get('gatcha_id')
    base_price = data.get('basePrice')
    end_date = data.get('endDate')

    # Controlla che tutti i parametri siano forniti
    if not all([seller_id, gatcha_id, base_price, end_date]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Creazione della nuova asta
    new_auction = Auction(
        gatcha_id=gatcha_id,
        seller_id=seller_id,
        base_price=base_price,
        end_date=end_date
    )
    db.session.add(new_auction)
    db.session.commit()
    
    return jsonify({"id": new_auction.id, "message": "Auction created successfully"}), 200



# Rotta per modificare un'asta esistente (solo admin)
@app.route('/modify', methods=['PATCH'])
#@jwt_required()
def modify_auction():
    #current_user = get_jwt_identity()
    #if current_user['role'] != 'admin':
    #    return jsonify({"error": "Not authorized"}), 403

    auction_id = request.args.get('auction_id')
    if not auction_id:
        return jsonify({"error": "Auction ID is required"}), 400

    # Trova l'asta da modificare
    auction = Auction.query.get(auction_id)
    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    # Aggiorna i campi specificati, se forniti
    seller_id = request.args.get('seller_id')
    gatcha_id = request.args.get('gatcha_id')
    end_date = request.args.get('endDate')
    base_price = request.args.get('basePrice')

    if seller_id:
        auction.seller_id = seller_id
    if gatcha_id:
        auction.gatcha_id = gatcha_id
    if end_date:
        auction.end_date = end_date
    if base_price:
        auction.base_price = base_price

    db.session.commit()
    return jsonify({"id": auction.id, "message": "Auction updated successfully"}), 200

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5008)
