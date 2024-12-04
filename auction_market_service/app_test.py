import os
from flask import Flask, request, jsonify , url_for, send_from_directory
import requests, time
from datetime import datetime
from requests.exceptions import HTTPError, ConnectionError
#from flask_bcrypt import Bcrypt
#from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
import uuid
import jwt  # PyJWT
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import re




public_key_path = os.getenv("PUBLIC_KEY_PATH")

app = Flask(__name__)

def mock_decode_jwt(token, public_key, algorithms, audience):
    # Simula una risposta di decodifica valida
    if token == "valid_token":
        return {
            "sub": "user1",
            "aud": audience,
            "exp": int(datetime.now().timestamp()) + 3600  # Token valido per un'ora
        }
    if token == "valid_token2":
        return {
            "sub": "user2",
            "aud": audience,
            "exp": int(datetime.now().timestamp()) + 3600  # Token valido per un'ora
        }
    if token == "valid_token3":
        return {
            "sub": "user3",
            "aud": audience,
            "exp": int(datetime.now().timestamp()) + 3600  # Token valido per un'ora
        }
    elif token == "expired_token":
        raise jwt.ExpiredSignatureError("Token expired")
    else:
        raise jwt.InvalidTokenError("Invalid token")



# Funzione per sanitizzare input
def sanitize_input(input_string):
    """Permette solo caratteri alfanumerici, trattini bassi e spazi."""
    if not input_string:
        return input_string
    return re.sub(r"[^\w\s-]", "", input_string)
def sanitize_input_gacha(input_string):
    """Permette solo caratteri alfanumerici, trattini bassi, spazi, trattini e punti."""
    if not input_string:
        return input_string
    return re.sub(r"[^\w\s\-.]", "", input_string)
    

# Definizione di check_and_close_auctions
# def check_and_close_auctions():
#     with app.app_context():
#         # Trova tutte le aste attive la cui data di fine è scaduta
#         expired_auctions = Auction.query.filter(Auction.status == 'active', Auction.end_date <= datetime.now()).all()

#         for auction in expired_auctions:
#             if auction.current_bid == 0:
#                 # Nessun partecipante: chiamare solo gacha_receive
#                 payload = {"auction_id": auction.id}
#                 # response = requests.post(f"http://auction_service:5008/gacha_receive", json=payload, timeout=10)
#                 # response.raise_for_status()
#                 response, status = auction_circuit_breaker.call('post', 'https://auction_service:5008/gacha_receive', payload, {},{}, True )
#                 if status != 200:
#                     app.logger.error(f"Errore durante gacha_receive per l'asta {auction.id}: {response}")
#             else:
#                 # Con partecipanti: chiamare tutte le funzioni
#                 payload = {"auction_id": auction.id}
#                     # Gacha Receive per trasferire il gacha al vincitore
#                     # gacha_response = requests.post(f"http://auction_service:5008/gacha_receive", json=payload, timeout=10)
#                     # gacha_response.raise_for_status()
#                 response, status = auction_circuit_breaker.call('post', 'https://auction_service:5008/gacha_receive', payload, {},{}, True )
#                 if status != 200:
#                     app.logger.error(f"Errore durante gacha_receive per l'asta {auction.id}: {response}")

                
#                     # Refund dei partecipanti perdenti
#                     # lost_response = requests.post(f"http://auction_service:5008/auction_lost", json=payload, timeout=10)
#                     # lost_response.raise_for_status()
#                 lost_response, status = auction_circuit_breaker.call('post', 'https://auction_service:5008/auction_lost', payload, {},{}, True )
#                 if status != 200:
#                     app.logger.error(f"Errore durante auction_lost per l'asta {auction.id}: {lost_response}")
#                     # Trasferire i fondi al venditore
#                 # terminated_response = requests.post(f"http://auction_service:5008/auction_terminated", json=payload, timeout=10)
#                 # terminated_response.raise_for_status()
#                 terminated_response, status = auction_circuit_breaker.call('post', 'https://auction_service:5008/auction_terminated', payload, {},{}, True )
#                 if status != 200:
#                     app.logger.error(f"Errore durante auction_terminated per l'asta {auction.id}: {terminated_response}")

#             # Cambia lo stato dell'asta a 'closed'
#             auction.status = 'closed'
#             db.session.commit()
#             app.logger.info(f"Asta {auction.id} chiusa correttamente.")

# # Configurazione dello Scheduler
# scheduler = BackgroundScheduler()
# scheduler.add_job(func=check_and_close_auctions, trigger="interval", seconds=60)  # Controlla ogni minuto

# @app.before_first_request
# def start_scheduler():
#     if not scheduler.running:
#         scheduler.start()

def mock_search_auction(auction_id):
        if auction_id == 100:
            return {}
        elif auction_id==10:
            return {
                "id": auction_id,
                "gacha_name": "Trial gacha",
                "seller_username": "user1",
                "winner_username": "user3",
                "current_bid": 0,
                "base_price": 10,
                "end_date": "15/12/24",
                "status": "active"
            }
        return {
            "id": auction_id,
            "gacha_name": "Trial gacha",
            "seller_username": "user1",
            "winner_username": "user3",
            "current_bid": 50,
            "base_price": 10,
            "end_date": "15/12/24",
            "status": "active"
        }

def mock_search_auctions(status):
        return [{
            "id": "1",
            "gacha_name": "Trial gacha",
            "seller_username": "user1",
            "winner_username": "user3",
            "current_bid": "50",
            "base_price": "10",
            "end_date": "15/12/24",
            "status": status
        }]
@app.route('/see', methods=['GET']) #controlli token no
def see_auctions():
    # Recupera l'header Authorization
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    access_token = auth_header.removeprefix("Bearer ").strip()

    # Leggi la chiave pubblica
    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Verifica il token con la chiave pubblica
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="auction_service")  
    except ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    # Token valido, procedi con la logica originale
    auction_id = request.args.get('auction_id')
    status = request.args.get('status', 'active')
    
    if auction_id:
        try:
            auction_id = int(auction_id)  # Prova a convertire auction_id in int
        except (TypeError, ValueError):
            return jsonify({"error": "auction_id must be an integer"}), 400
        auction= mock_search_auction(auction_id)
        if auction:
            return jsonify(auction), 200
        else:
            return jsonify({"error": "Auction not found"}), 404

    # Se il valore di auction_id non è fornito allora ritorna tutte le aste attive
    auctions = mock_search_auctions(status)
    return jsonify(auctions), 200

def mock_find_auction(gacha_name,seller_username, status):
    if gacha_name == "already_present":
        return True
    return False
def mock_new_auction(gacha_name,seller_username, winner_username, base_price, end_date):
    return jsonify({'msg' : 'Correcrtly inserted'})
def mock_profile(seller_username, gacha_name):
    return jsonify({'msg':'Gacha correctly added'}), 200
@app.route('/create', methods=['POST']) #controlli sul seller 
def create_auction():
    # Recupera l'header Authorization
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    access_token = auth_header.removeprefix("Bearer ").strip()

    # Leggi la chiave pubblica
    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Decodifica e verifica il token
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="auction_service")
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    # Legge i dati dalla richiesta JSON
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON or missing Content-Type header"}), 400
    
    # Recupera i parametri dall'oggetto JSON
    seller_username = sanitize_input(data.get('seller_username'))
    gacha_name = sanitize_input_gacha(data.get('gacha_name'))
    base_price = data.get('basePrice')
    end_date = data.get('endDate')

      # Controlla che tutti i parametri siano forniti
    if not all([seller_username, gacha_name, base_price, end_date]):
        return jsonify({"error": "Missing required parameters"}), 400
    
        # Controlla che base_price sia un numero valido
    if not isinstance(base_price, (int, float)) or base_price <= 0:
        return jsonify({"error": "Base price must be a positive number"}), 400

    sanitized_value = float(base_price)
    if sanitized_value <= 0:
        return jsonify({"error": "base price must be higher than"}), 400
    # Controlla che il ruolo dell'utente sia corretto
    if decoded_token.get('sub') != seller_username:
        return jsonify({"error": "Unauthorized access, only the seller can create this auction"}), 403
    existing_auction = mock_find_auction(gacha_name, seller_username, 'active')
    if existing_auction:
        return jsonify({"error": "An active auction already exists for this gatcha"}), 400

    # Controlla che end_date sia una data valida e futura
    try:
        end_date = datetime.fromisoformat(end_date)
        if end_date <= datetime.now():
            return jsonify({"error": "End date must be in the future"}), 400
    except ValueError:
        return jsonify({"error": "Invalid end date format. Use ISO format, e.g., '2024-12-31T23:59:59'"}), 400


    mock_new_auction( gacha_name=gacha_name,
        seller_username=seller_username,
        winner_username = seller_username,
        base_price=base_price,
        end_date=end_date)

    response, status = mock_profile(seller_username, gacha_name)
    if status != 200:
        return jsonify({"error": f"Error removing gacha from profile: {response}"}), status
    return jsonify({"id": 1, "message": "Auction created successfully"}), 200



# Rotta per modificare un'asta esistente (solo admin) -> NON FACCIO CONTROLLI PERCHE' QUESTA OP LA FA SOLO L'ADMIN QUINDI DOVREBBE ESSERE CONSAPEVOLE
@app.route('/modify', methods=['PATCH'])
#@jwt_required()
def modify_auction():
    # Recupera l'header Authorization
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    access_token = auth_header.removeprefix("Bearer ").strip()

    # Leggi la chiave pubblica
    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Decodifica e verifica il token
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="auction_service")
        
        # Verifica che il ruolo sia admin
        user_role = decoded_token.get("scope")
        if user_role != "admin":
            return jsonify({"error": "Not authorized"}), 403
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    auction_id = request.args.get('auction_id')
    if not auction_id:
        return jsonify({"error": "Auction ID is required"}), 400

    # Trova l'asta da modificare
    auction = mock_search_auction(auction_id)
    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    # Aggiorna i campi specificati, se forniti
    seller_username = request.args.get('seller_username')
    gacha_name = request.args.get('gacha_name')
    end_date = request.args.get('endDate')
    base_price = request.args.get('basePrice')

    if seller_username:
        auction['seller_username'] = seller_username
    if gacha_name:
        auction['gacha_name'] = gacha_name
    if end_date:
        auction['end_date'] = end_date
    if base_price:
        auction['base_price'] = base_price

    # db.session.commit()
    return jsonify({"id": auction.id, "message": "Auction updated successfully"}), 200
def mock_find_bid(auction_id,bidder_username):
    if auction_id == 20:
        return {
        "bid_amount" : 1
    } 
    elif auction_id == 100 or auction_id == 10:
        return{}
    return {
        "bid_amount" : 15
    }

def mock_find_bids(auction_id):
    if auction_id == 20:
        return [{
        "username" : 'user1',
        "bid_amount" : 0
    }]
    elif auction_id == 100 or auction_id == 10:
        return[]
    return [{
        "username" : 'user1',
        "bid_amount" : 15
    }]

def mock_payment(payer, receiver , amount):
    return jsonify({'msg': 'Correctly payed'}), 200

def mock_new_bid(auction_id, bidder_username, new_bid):
    return jsonify({
        'auction_id' : auction_id,
        'bidder' : bidder_username,
        'new_bid' : new_bid
    })
@app.route('/bid', methods=['PATCH']) #controlli token
def bid_for_auction():
    # Recupera l'header Authorization
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    access_token = auth_header.removeprefix("Bearer ").strip()

    # Leggi la chiave pubblica
    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Decodifica e verifica il token
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="auction_service")

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
    # Recupera i parametri dalla query string
    bidder_username = sanitize_input(request.args.get('username'))
    auction_id = request.args.get('auction_id')
    new_bid = request.args.get('newBid')

    # Controlla che tutti i parametri siano presenti
    if not all([bidder_username, auction_id, new_bid]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        auction_id = int(auction_id)  # Prova a convertire auction_id in int
    except (TypeError, ValueError):
        return jsonify({"error": "auction_id must be an integer"}), 400
    try:
        new_bid = float(new_bid)  # Prova a convertire new_bid in float
    except (TypeError, ValueError):
        return jsonify({"error": "newBid must be a float"}), 400

    # Controlla che il ruolo dell'utente sia corretto
    if decoded_token.get('sub') != bidder_username:
        return jsonify({"error": "Unauthorized access, only the bidder can create a bid for the auction"}), 403


    # Trova l'asta corrispondente
    auction=mock_search_auction(auction_id)
    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    if auction['status'] != 'active':
        return jsonify({"error": "Cannot place a bid on a closed or inactive auction"}), 400
    
    # Controlla che il creatore dell'asta non possa fare una bid
    if auction['seller_username'] == bidder_username:
        return jsonify({"error": "You cannot bid on your own auction"}), 400

    if auction['winner_username'] == bidder_username:
        return jsonify({"error": "You are already the highest bidder"}), 400

    if new_bid <= auction['base_price']:
        return jsonify({"error": "Bid must be higher than the base_price"}), 400
    # Controlla che l'offerta sia valida
    if new_bid <= auction['current_bid']:
        return jsonify({"error": "Bid must be higher than the current bid"}), 400
    
    # Trova l'offerta precedente dell'utente per questa asta
    previous_bid = mock_find_bid(auction_id,bidder_username)
    # Calcola la differenza da sottrarre
    bid_difference = new_bid - (previous_bid['bid_amount'] if previous_bid else 0)

    if bid_difference <= 0:
        return jsonify({"error": "New bid must be higher than your previous bid"}), 400

    payment_response, status = mock_payment(bidder_username, "system", bid_difference)
    if status != 200:
        return jsonify({"error": f"Payment failed: {payment_response}"}), status

    # Aggiorna o crea l'offerta dell'utente nella tabella `bids`
    if previous_bid:
        previous_bid['bid_amount'] = new_bid
        previous_bid['bid_time'] = datetime.now()
    else:
        new_bid_entry = mock_new_bid(auction_id, bidder_username, new_bid)
        
    # Aggiorna l'offerta corrente e il vincitore nell'asta
    auction['current_bid'] = new_bid
    auction['winner_username'] = bidder_username
    
    return jsonify({"message": "New bid set"}), 200

def mock_profile_insertgacha(winner, gacha_Name, date):
    return jsonify({'msg': f'gacha {gacha_Name} inserted'}), 200

@app.route('/gacha_receive', methods=['POST'])
def gacha_receive():

    # Recupera i parametri dall'oggetto JSON
    data = request.get_json()
    auction_id = data.get('auction_id')

    # Verifica che auction_id sia fornito
    if not auction_id:
        return jsonify({"error": "Invalid input: auction_id is required"}), 400
    if not isinstance(auction_id, (int, float)):
        return jsonify({"error": "auction id must be int or float"}), 400
    # Recupera l'asta dal database usando l'ID
    auction= mock_search_auction(auction_id)
    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    # Verifica che l'asta abbia un vincitore e un nome gacha associato
    if not auction['winner_username'] or not auction['gacha_name']:
        return jsonify({"error": "Auction has no winner or gacha_name"}), 400

    winner_username = auction['winner_username']
    gacha_name = auction['gacha_name']

    # Crea il payload per la chiamata al servizio di profile_setting



    payment_response, status = mock_profile_insertgacha(winner_username, gacha_name, datetime.now().isoformat() )
    if status != 200:
        return jsonify({f"error": "Profile service failed", "details": {payment_response}}), status
    return jsonify({"message": "Gacha correctly received"}), 200

@app.route('/auction_lost', methods=['POST'])
def auction_lost():

    # Recupera i parametri dal corpo JSON
    data = request.get_json()
    auction_id = data.get('auction_id')

    if not auction_id:
        return jsonify({"error": "Missing auction_id"}), 400
    if not isinstance(auction_id, (int, float)):
        return jsonify({"error": "auction id must be int or float"}), 400

    # Trova l'asta corrispondente
    auction = mock_search_auction(auction_id)
    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    # Controlla che l'asta sia conclusa PER ORA LO DISABILITO, SIA PER TESTING MA ANCHE PER CAPIRE COME DOBBIAMO GESTIRE QUANDO L'ASTA E' CHIUSA (1: SE C'E' UNO SCRIPT CHE GIRA CONTROLLA CHE L'ASTA
    # SIA CHIUSA E CHIAMA L'API (CONTROLLO SULLO SCRIPT), 2: SE INVECE LA CHIAMIAMO NOI
    # if auction.status != 'closed':
    #     return jsonify({"error": "Auction is not closed"}), 400

    # Ottieni tutti i partecipanti all'asta (dalla tabella `bids`)
    bids = mock_find_bids(auction_id)
    if not bids:
        return jsonify({"error": "No bids found for this auction"}), 404

    # Itera su tutti i partecipanti e fai il refund ai non vincitori
    failed_refunds = []
    successful_refunds = []

    for bid in bids:
        if bid['username'] != auction['winner_username']:
            payment_response , status = mock_payment("auction_system", bid['username'], bid['bid_amount'])
            if status != 200:
                failed_refunds.append({"username": bid['username'], "error": f"Payment failed: {payment_response}"})
            else:
                successful_refunds.append({
                    "username": bid['username'],
                    "amount": bid['bid_amount']
                })

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
    if not isinstance(auction_id, (int, float)):
        return jsonify({"error": "auction id must be int or float"}), 400


    # Trova l'asta corrispondente
    auction = mock_search_auction(auction_id)
    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    # Controlla se l'asta è conclusa SOLITO DISCORSO
    #if auction.status != 'closed':
    #    return jsonify({"error": "Auction is not closed"}), 400

    # Controlla se l'asta ha un current_bid di 0
    if auction['current_bid'] == 0:
        return jsonify({"error": "Auction has no valid bids to transfer, no money sent from system to seller :("}), 400

    payment_response , status = mock_payment("system", auction['seller_username'], auction['current_bid'])
    if status != 200:
        return jsonify({"error": f"Payment failed: {payment_response}"}), status

    # Ritorna i dettagli della transazione completata
    return jsonify({
        "message": "Money correctly transferred to seller",
        "transaction_details": {
            "payer_us": "auction_system",
            "receiver_us": auction['seller_username'],
            "amount": auction['current_bid']
        }
    }), 200

def mock_gacha_receive(auction_id):
    return jsonify({"message": "Gacha correctly received"}), 200
@app.route('/close_auction', methods=['POST'])
def close_auction():
    # Recupera l'header Authorization
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    access_token = auth_header.removeprefix("Bearer ").strip()

    # Leggi la chiave pubblica
    with open(public_key_path, 'r') as key_file:
        public_key = key_file.read()

    try:
        # Decodifica e verifica il token
        decoded_token = mock_decode_jwt(access_token, public_key, algorithms=["RS256"], audience="auction_service")
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    data = request.get_json()
    auction_id = data.get('auction_id')
    username = sanitize_input(data.get('username'))

    # Controlla che auction_id e username siano forniti
    if not auction_id:
        return jsonify({"error": "Auction ID is required"}), 400
    if not username:
        return jsonify({"error": "Username is required"}), 400
    if not isinstance(auction_id, (int, float)):
        return jsonify({"error": "auction id must be int or float"}), 400

    # Verifica che l'username sia quello del token
    if decoded_token.get('sub') != username:
        return jsonify({"error": "Unauthorized access, token username mismatch"}), 403

    # Recupero l'asta dal database
    auction = mock_search_auction(auction_id)
    if not auction:
        return jsonify({"error": "Auction not found"}), 404

    # Verifica che l'utente sia il seller dell'asta
    if auction['seller_username'] != username:
        return jsonify({"error": "Unauthorized access, only the seller can close this auction"}), 403

    # Controllo se l'asta è già chiusa
    if auction['status'] != 'active':
        return jsonify({"error": "Auction is already closed or inactive"}), 400

    # Verifico se ci sono offerte associate all'asta
    bids = mock_find_bids(auction_id)
    if bids:
        return jsonify({"error": "Auction cannot be closed because it has bids"}), 400

    # Nessuna offerta: chiudo l'asta
    auction['status'] = 'closed'

    response, status = mock_gacha_receive(auction_id)
    if status != 200:
        return jsonify({"error": "Failed to return gacha to seller", "details": response}), 500

    # Salvo i cambiamenti nel database

    return jsonify({"message": "Auction closed successfully", "auction_id": auction_id}), 200

