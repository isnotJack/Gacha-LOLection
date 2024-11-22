import os
from flask import Flask, request, jsonify , url_for, send_from_directory
import requests
from datetime import datetime
from requests.exceptions import HTTPError, ConnectionError
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
#from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler




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
    gacha_name = db.Column(db.String(50))
    seller_username = db.Column(db.String(50))
    winner_username = db.Column(db.String(50))
    current_bid = db.Column(db.Float, default=0.0)
    base_price = db.Column(db.Float, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(10), default='active')

    def to_dict(self):
        return {
            "id": self.id,
            "gacha_name": self.gacha_name,
            "seller_username": self.seller_username,
            "winner_username": self.winner_username,
            "current_bid": self.current_bid,
            "base_price": self.base_price,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status
        }

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'user' or 'admin'

class Bid(db.Model):
    __tablename__ = 'bids'
    id = db.Column(db.Integer, primary_key=True)
    auction_id = db.Column(db.Integer, db.ForeignKey('auctions.id', ondelete='CASCADE'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    bid_amount = db.Column(db.Float, nullable=False)
    bid_time = db.Column(db.DateTime, default=datetime.now)

    auction = db.relationship('Auction', backref=db.backref('bids', cascade='all, delete'))

# Definizione di check_and_close_auctions
def check_and_close_auctions():
    with app.app_context():
        # Trova tutte le aste attive la cui data di fine è scaduta
        expired_auctions = Auction.query.filter(Auction.status == 'active', Auction.end_date <= datetime.now()).all()

        for auction in expired_auctions:
            if auction.current_bid == 0:
                # Nessun partecipante: chiamare solo gacha_receive
                payload = {"auction_id": auction.id}
                try:
                    response = requests.post(f"http://auction_service:5008/gacha_receive", json=payload, timeout=10)
                    response.raise_for_status()
                except requests.RequestException as e:
                    app.logger.error(f"Errore durante gacha_receive per l'asta {auction.id}: {str(e)}")
            else:
                # Con partecipanti: chiamare tutte le funzioni
                payload = {"auction_id": auction.id}
                try:
                    # Gacha Receive per trasferire il gacha al vincitore
                    gacha_response = requests.post(f"http://auction_service:5008/gacha_receive", json=payload, timeout=10)
                    gacha_response.raise_for_status()
                except requests.RequestException as e:
                    app.logger.error(f"Errore durante gacha_receive per l'asta {auction.id}: {str(e)}")

                try:
                    # Refund dei partecipanti perdenti
                    lost_response = requests.post(f"http://auction_service:5008/auction_lost", json=payload, timeout=10)
                    lost_response.raise_for_status()
                except requests.RequestException as e:
                    app.logger.error(f"Errore durante auction_lost per l'asta {auction.id}: {str(e)}")

                try:
                    # Trasferire i fondi al venditore
                    terminated_response = requests.post(f"http://auction_service:5008/auction_terminated", json=payload, timeout=10)
                    terminated_response.raise_for_status()
                except requests.RequestException as e:
                    app.logger.error(f"Errore durante auction_terminated per l'asta {auction.id}: {str(e)}")

            # Cambia lo stato dell'asta a 'closed'
            auction.status = 'closed'
            db.session.commit()
            app.logger.info(f"Asta {auction.id} chiusa correttamente.")

# Configurazione dello Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_close_auctions, trigger="interval", seconds=60)  # Controlla ogni minuto

@app.before_first_request
def start_scheduler():
    if not scheduler.running:
        scheduler.start()

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
    if data is None:
        return jsonify({"error": "Invalid JSON or missing Content-Type header"}), 400

    
    
    # Recupera i parametri dall'oggetto JSON
    seller_username = data.get('seller_username')
    gacha_name = data.get('gacha_name')
    base_price = data.get('basePrice')
    end_date = data.get('endDate')

    existing_auction = Auction.query.filter_by(gacha_name=gacha_name, seller_username=seller_username, status='active').first()
    if existing_auction:
        return jsonify({"error": "An active auction already exists for this gatcha"}), 400


    # Controlla che tutti i parametri siano forniti
    if not all([seller_username, gacha_name, base_price, end_date]):
        return jsonify({"error": "Missing required parameters"}), 400
    
        # Controlla che base_price sia un numero valido
    if not isinstance(base_price, (int, float)) or base_price <= 0:
        return jsonify({"error": "Base price must be a positive number"}), 400

    # Controlla che end_date sia una data valida e futura
    try:
        end_date = datetime.fromisoformat(end_date)
        if end_date <= datetime.now():
            return jsonify({"error": "End date must be in the future"}), 400
    except ValueError:
        return jsonify({"error": "Invalid end date format. Use ISO format, e.g., '2024-12-31T23:59:59'"}), 400

    # Creazione della nuova asta
    new_auction = Auction(
        gacha_name=gacha_name,
        seller_username=seller_username,
        winner_username = seller_username,
        base_price=base_price,
        end_date=end_date
    )

    profile_service_url = "http://profile_setting:5003/deleteGacha"
    payload = {
        "username": seller_username,
        "gacha_name": gacha_name
    }

    try:
        response = requests.delete(profile_service_url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return jsonify({"Error": "Time out expired"}), 408
    except ConnectionError:
        return jsonify({"error": "Profile Service is down"}), 404
    except HTTPError as e:
        return jsonify({"error": f"Error removing gacha from profile: {str(e)}"}), response.status_code

    db.session.add(new_auction)
    db.session.commit()
    
    return jsonify({"id": new_auction.id, "message": "Auction created successfully"}), 200



# Rotta per modificare un'asta esistente (solo admin) -> NON FACCIO CONTROLLI PERCHE' QUESTA OP LA FA SOLO L'ADMIN QUINDI DOVREBBE ESSERE CONSAPEVOLE
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
    seller_username = request.args.get('seller_username')
    gacha_name = request.args.get('gacha_name')
    end_date = request.args.get('endDate')
    base_price = request.args.get('basePrice')

    if seller_username:
        auction.seller_username = seller_username
    if gacha_name:
        auction.gacha_name = gacha_name
    if end_date:
        auction.end_date = end_date
    if base_price:
        auction.base_price = base_price

    db.session.commit()
    return jsonify({"id": auction.id, "message": "Auction updated successfully"}), 200

@app.route('/bid', methods=['PATCH'])
def bid_for_auction():
    # Recupera i parametri dalla query string
    bidder_username = request.args.get('username') 
    auction_id = request.args.get('auction_id')
    new_bid = request.args.get('newBid', type=float)

    # Controlla che tutti i parametri siano presenti
    if not all([bidder_username, auction_id, new_bid]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Trova l'asta corrispondente
    auction = Auction.query.get(auction_id)
    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    if auction.status != 'active':
        return jsonify({"error": "Cannot place a bid on a closed or inactive auction"}), 400
    
    if auction.winner_username == bidder_username:
        return jsonify({"error": "You are already the highest bidder"}), 400

    # Controlla che l'offerta sia valida
    if new_bid <= auction.current_bid:
        return jsonify({"error": "Bid must be higher than the current bid"}), 400
    
    if new_bid <= auction.base_price:
        return jsonify({"error": "Bid must be higher than the base_price"}), 400

    # Trova l'offerta precedente dell'utente per questa asta
    previous_bid = Bid.query.filter_by(auction_id=auction_id, username=bidder_username).first()

    # Calcola la differenza da sottrarre
    bid_difference = new_bid - (previous_bid.bid_amount if previous_bid else 0)

    if bid_difference <= 0:
        return jsonify({"error": "New bid must be higher than your previous bid"}), 400

    payment_service_url = "http://payment_service:5006/pay"
    payload = {
        "payer_us": bidder_username,
        "receiver_us": "auction_system",
        "amount": bid_difference
    }

    try:
        payment_response = requests.post(payment_service_url, data=payload, timeout=10)
        payment_response.raise_for_status()
    except requests.exceptions.Timeout:
        return jsonify({"Error": "Time out expired"}), 408
    except requests.ConnectionError:
        return jsonify({"error": "Payment Service is down"}), 404
    except requests.HTTPError as e:
        return jsonify({"error": f"Payment failed: {str(e)}"}), payment_response.status_code

    # Aggiorna o crea l'offerta dell'utente nella tabella `bids`
    if previous_bid:
        previous_bid.bid_amount = new_bid
        previous_bid.bid_time = datetime.now()
    else:
        new_bid_entry = Bid(auction_id=auction_id, username=bidder_username, bid_amount=new_bid)
        db.session.add(new_bid_entry)

    # Aggiorna l'offerta corrente e il vincitore nell'asta
    auction.current_bid = new_bid
    auction.winner_username = bidder_username
    db.session.commit()

    return jsonify({"message": "New bid set"}), 200


@app.route('/gacha_receive', methods=['POST'])
def gacha_receive():
    # Recupera i parametri dall'oggetto JSON
    data = request.get_json()
    auction_id = data.get('auction_id')

    # Verifica che auction_id sia fornito
    if not auction_id:
        return jsonify({"error": "Invalid input: auction_id is required"}), 400

    # Recupera l'asta dal database usando l'ID
    auction = Auction.query.get(auction_id)

    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    # Verifica che l'asta abbia un vincitore e un nome gacha associato
    if not auction.winner_username or not auction.gacha_name:
        return jsonify({"error": "Auction has no winner or gacha_name"}), 400

    winner_username = auction.winner_username
    gacha_name = auction.gacha_name

    # Crea il payload per la chiamata al servizio di profile_setting
    profile_service_url = "http://profile_setting:5003/insertGacha"
    payload = {
        "username": winner_username,  # Nome del vincitore
        "gacha_name": gacha_name,   # Nome del gacha
        "collected_date": datetime.now().isoformat()  # Usa il formato ISO per la data
    }

    try:
        response = requests.post(profile_service_url, json=payload, timeout=10)
        # Controlla la risposta del servizio profile_setting
        if response.status_code == 200:
            return jsonify({"message": "Gacha correctly received"}), 200
        else:
            return jsonify({"error": "Profile service failed", "details": response.text}), 404
    except requests.exceptions.Timeout:
        return jsonify({"Error": "Time out expired"}), 408
    except requests.exceptions.RequestException as e:
        # Gestisce errori di rete o problemi con il servizio profile_setting
        return jsonify({"error": "Profile service is down", "details": str(e)}), 404

@app.route('/auction_lost', methods=['POST'])
def auction_lost():
    # Recupera i parametri dal corpo JSON
    data = request.get_json()
    auction_id = data.get('auction_id')

    if not auction_id:
        return jsonify({"error": "Missing auction_id"}), 400

    # Trova l'asta corrispondente
    auction = Auction.query.get(auction_id)
    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    # Controlla che l'asta sia conclusa PER ORA LO DISABILITO, SIA PER TESTING MA ANCHE PER CAPIRE COME DOBBIAMO GESTIRE QUANDO L'ASTA E' CHIUSA (1: SE C'E' UNO SCRIPT CHE GIRA CONTROLLA CHE L'ASTA
    # SIA CHIUSA E CHIAMA L'API (CONTROLLO SULLO SCRIPT), 2: SE INVECE LA CHIAMIAMO NOI
    # if auction.status != 'closed':
    #     return jsonify({"error": "Auction is not closed"}), 400

    # Ottieni tutti i partecipanti all'asta (dalla tabella `bids`)
    bids = Bid.query.filter_by(auction_id=auction_id).all()
    if not bids:
        return jsonify({"error": "No bids found for this auction"}), 404

    # Itera su tutti i partecipanti e fai il refund ai non vincitori
    payment_service_url = "http://payment_service:5006/pay"
    failed_refunds = []
    successful_refunds = []

    for bid in bids:
        if bid.username != auction.winner_username:
            # Calcola il refund per ogni non vincitore
            refund_payload = {
                "payer_us": "auction_system",  # Sistema come pagatore
                "receiver_us": bid.username,  # Utente come destinatario
                "amount": bid.bid_amount      # Refund del totale offerto
            }

            try:
                payment_response = requests.post(payment_service_url, data=refund_payload, timeout=10)
                payment_response.raise_for_status()
                successful_refunds.append({
                    "username": bid.username,
                    "amount": bid.bid_amount
                })
            except requests.exceptions.Timeout:
                return jsonify({"Error": "Time out expired"}), 408
            except requests.ConnectionError:
                failed_refunds.append({"username": bid.username, "error": "Payment service down"})
            except requests.HTTPError as e:
                failed_refunds.append({"username": bid.username, "error": f"Payment failed: {str(e)}"})

    # Ritorna i dettagli delle transazioni
    return jsonify({
        "message": "Refund process completed",
        "successful_refunds": successful_refunds,
        "failed_refunds": failed_refunds
    }), 200

@app.route('/auction_terminated', methods=['POST'])
def auction_terminated():
    # Recupera i parametri dal corpo JSON
    data = request.get_json()
    auction_id = data.get('auction_id')

    if not auction_id:
        return jsonify({"error": "Missing auction_id"}), 400

    # Trova l'asta corrispondente
    auction = Auction.query.get(auction_id)
    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    # Controlla se l'asta è conclusa SOLITO DISCORSO
    #if auction.status != 'closed':
    #    return jsonify({"error": "Auction is not closed"}), 400

    # Controlla se l'asta ha un current_bid di 0
    if auction.current_bid == 0:
        return jsonify({"error": "Auction has no valid bids to transfer, no money sent from system to seller :("}), 400

    # Recupera i dettagli per la transazione
    payment_service_url = "http://payment_service:5006/pay"
    transfer_payload = {
        "payer_us": "auction_system",  # Il sistema paga il seller
        "receiver_us": auction.seller_username,  # Il creatore dell'asta riceve
        "amount": auction.current_bid  # L'importo totale offerto dal vincitore
    }

    try:
        payment_response = requests.post(payment_service_url, data=transfer_payload, timeout=10)
        payment_response.raise_for_status()
    except requests.ConnectionError:
        return jsonify({"error": "Payment Service is down"}), 404
    except requests.HTTPError as e:
        return jsonify({"error": f"Payment failed: {str(e)}"}), payment_response.status_code

    # Ritorna i dettagli della transazione completata
    return jsonify({
        "message": "Money correctly transferred to seller",
        "transaction_details": {
            "payer_us": "auction_system",
            "receiver_us": auction.seller_username,
            "amount": auction.current_bid
        }
    }), 200



if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=5008)
