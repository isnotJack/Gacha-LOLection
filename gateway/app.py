import requests, time
import os
from flask import Flask, request, make_response, jsonify, send_file
from requests.exceptions import ConnectionError, HTTPError
from werkzeug.exceptions import NotFound
from io import BytesIO


ALLOWED_AUTH_OP ={'signup', 'login', 'logout', 'delete'}
SINGUP_URL = 'http://auth_service:5002/signup'
LOGIN_URL = 'http://auth_service:5002/login'
LOGOUT_URL = 'http://auth_service:5002/logout'
DELETE_URL = 'http://auth_service:5002/delete'

ALLOWED_PROF_OP ={'modify','checkprofile', 'retrieve_gachacollection', 'info_gachacollection'}
MODIFY_URL = 'http://profile_setting:5003/modify'
CHECK_URL = 'http://profile_setting:5003/checkprofile'
RETRIEVE_URL = 'http://profile_setting:5003/retrieve_gachacollection'
INFO_URL = 'http://profile_setting:5003/info_gachacollection'

ALLOWED_AUCTION_OP = {'see', 'create', 'modify', 'bid','gatcha_receive'} 
AUCTION_BASE_URL = 'http://auction_service:5008'
SEE_AUCTION_URL = f'{AUCTION_BASE_URL}/see'
CREATE_AUCTION_URL = f'{AUCTION_BASE_URL}/create'
MODIFY_AUCTION_URL = f'{AUCTION_BASE_URL}/modify'
BID_AUCTION_URL = f'{AUCTION_BASE_URL}/bid'

GACHAROLL_URL = 'http://gacha_roll:5007/gacharoll'
GACHA_IMAGE_URL = 'http://gachasystem:5004/uploads/'

PROFILE_IMAGE_URL = 'http://profile_setting:5003/uploads/'

BUYCURRENCY_URL = 'http://payment_service:5006/buycurrency'
#Per gestione immagini
def get_mime_type(extension):
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp',
    }
    return mime_types.get(extension.lower(), 'application/octet-stream')  # Tipo predefinito se non trovato

app = Flask(__name__, instance_relative_config=True)
def create_app():
    return app

@app.route('/auth_service/<op>', methods=['POST', 'DELETE'])
def auth(op):
    if op not in ALLOWED_AUTH_OP:
        return make_response(f'Invalid operation {op}'),400
    if op == 'signup':
        #Dati che arrivano al gateway da un form lato client
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        url = SINGUP_URL
        params = { 
            'username' : username,
            'password' : password,
            'email' : email
            }
    elif op =='login':
        username = request.form.get('username')
        password = request.form.get('password')
        url = LOGIN_URL
        params = { 
            'username' : username,
            'password' : password,
            }
    elif op == 'delete':
        username = request.form.get('username')
        password = request.form.get('password')
        url = DELETE_URL
        params = { 
            'username' : username,
            'password' : password,
            }
    elif op == 'logout':
        url = LOGOUT_URL
        params = {}
        jwt_token = request.headers.get('Authorization')  # Supponiamo che il token JWT sia passato nei headers come 'Authorization'
        headers = {
            'Authorization': jwt_token  # Usa il token JWT ricevuto nell'header della richiesta
        }
    try:
        if(op == 'login' or op=='signup'):
            x = requests.post(url, json=params)
        elif (op == 'logout'):
            x = requests.delete(url, headers=headers)
        else:
            x = requests.delete(url, json=params)
        x.raise_for_status()
        res = x.json()
        return res
    except ConnectionError:
        try:
            if(op == 'login' or op=='signup'):
                x = requests.post(url, json=params)
            elif (op == 'logout'):
                x = requests.delete(url, headers=headers)
            else:
                x = requests.delete(url, json=params)
            x.raise_for_status()
            res = x.json()
            return res
        except ConnectionError:
            return make_response("Authentication Service is down\n",404)
        except HTTPError:
            return make_response(x.content, x.status_code)
        return res
    except HTTPError:
        return make_response(x.content, x.status_code)

@app.route('/profile_setting/<op>', methods=['GET', 'PATCH'])
def profile_setting(op):
    if op not in ALLOWED_PROF_OP:
        return make_response(f'Invalid operation {op}'),400
    if op == 'modify':
        #Dati che arrivano al gateway da un form lato client
        username = request.form.get('username')
        value = request.form.get('value')
        field = request.form.get('field')
        url = MODIFY_URL
        params = { 
            'username' : username,
            'field' : field,
            'value' : value
            }
    elif op =='checkprofile':
        username = request.args.get('username')
        url = CHECK_URL + f"?username={username}"
        jwt_token = request.headers.get('Authorization')  # Supponiamo che il token JWT sia passato nei headers come 'Authorization'
        headers = {
            'Authorization': jwt_token  # Usa il token JWT ricevuto nell'header della richiesta
        }
    elif op == 'retrieve_gachacollection':
        username = request.args.get('username')
        url = RETRIEVE_URL + f"?username={username}"
        jwt_token = request.headers.get('Authorization')  # Supponiamo che il token JWT sia passato nei headers come 'Authorization'
        headers = {
            'Authorization': jwt_token  # Usa il token JWT ricevuto nell'header della richiesta
        }
    elif op == 'info_gachacollection':
        username = request.args.get('username')
        gatcha_id = request.args.get('gatcha_id')
        url = RETRIEVE_URL + f"?username={username}&gatcha_id={gatcha_id}"
        jwt_token = request.headers.get('Authorization')  # Supponiamo che il token JWT sia passato nei headers come 'Authorization'
        headers = {
            'Authorization': jwt_token  # Usa il token JWT ricevuto nell'header della richiesta
        }
    try:
        if(op == 'modify'):
            x = requests.patch(url, json=params)
        else:
            x = requests.get(url, headers=headers)
        x.raise_for_status()
        res = x.json()
        return res
    except ConnectionError:
        try:
            if(op == 'modify'):
                x = requests.patch(url, json=params)
            else:
                x = requests.get(url, headers=headers)
            x.raise_for_status()
            res = x.json()
            return res
        except ConnectionError:
            return make_response("Profile Service is down\n",404)
        except HTTPError:
            return make_response(x.content, x.status_code)
        return res
    except HTTPError:
        return make_response(x.content, x.status_code)

@app.route('/auction_service/<op>', methods=['GET', 'POST', 'PATCH'])
def auction_service(op):
    if op not in ALLOWED_AUCTION_OP:
        return jsonify({"error": f"Invalid operation '{op}'"}), 400

    # Operazione "see"
    if op == 'see':
        auction_id = request.args.get('auction_id')  # Recupera auction_id dai parametri della query
        status = request.args.get('status', 'active')  # Status predefinito a 'active'

        # Costruisce l'URL con i parametri corretti
        url = f'{SEE_AUCTION_URL}?status={status}'
        if auction_id:
            url += f'&auction_id={auction_id}'

        try:
            response = requests.get(url)
            response.raise_for_status()
            return jsonify(response.json())  # Wrappa la lista in jsonify
        except ConnectionError:
            return jsonify({"error": "Auction Service is down"}), 404
        except HTTPError as e:
            return jsonify({"error": str(e)}), response.status_code

    # Operazione "create"
    elif op == 'create':
        try:
            data = request.get_json()  # Recupera i parametri dal corpo JSON
            seller_id = data.get('seller_id')
            gatcha_id = data.get('gatcha_id')
            base_price = data.get('basePrice')
            end_date = data.get('endDate')

            # Verifica che tutti i parametri richiesti siano presenti
            if not all([seller_id, gatcha_id, base_price, end_date]):
                return jsonify({"error": "Missing required parameters"}), 400

            url = CREATE_AUCTION_URL
            response = requests.post(url, json=data)
            response.raise_for_status()
            return jsonify(response.json())  # Wrappa la risposta in jsonify
        except ConnectionError:
            return jsonify({"error": "Auction Service is down"}), 404
        except HTTPError as e:
            return jsonify({"error": str(e)}), response.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif op == 'modify':
        # Recupera i parametri dal JSON del client
        data = request.get_json()  
        auction_id = data.get('auction_id')
        seller_id = data.get('seller_id')
        gatcha_id = data.get('gatcha_id')
        base_price = data.get('basePrice')
        end_date = data.get('endDate')

        # Controlla che auction_id sia presente
        if not auction_id:
            return jsonify({"error": "Auction ID is required"}), 400

        # Costruisce l'URL con i parametri come query string
        url = f'{MODIFY_AUCTION_URL}?auction_id={auction_id}'
        if seller_id:
            url += f'&seller_id={seller_id}'
        if gatcha_id:
            url += f'&gatcha_id={gatcha_id}'
        if base_price:
            url += f'&basePrice={base_price}'
        if end_date:
            url += f'&endDate={end_date}'

        try:
            response = requests.patch(url)  # Nessun JSON, tutto passa come query string
            response.raise_for_status()
            return jsonify(response.json())  # Wrappa la risposta in jsonify
        except ConnectionError:
            return jsonify({"error": "Auction Service is down"}), 404
        except HTTPError as e:
            return jsonify({"error": str(e)}), response.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif op == 'bid':
        # Recupera i parametri dal JSON del client
        data = request.get_json()
        bidder_id = data.get('bidder_id')
        auction_id = data.get('auction_id')
        new_bid = data.get('newBid')

        # Controlla che tutti i parametri siano presenti
        if not all([bidder_id, auction_id, new_bid]):
            return jsonify({"error": "Missing required parameters"}), 400

        # Costruisce l'URL
        url = f'{AUCTION_BASE_URL}/bid'

        try:
            response = requests.patch(url, json=data)
            response.raise_for_status()
            return jsonify(response.json())  # Wrappa la risposta in jsonify
        except ConnectionError:
            return jsonify({"error": "Auction Service is down"}), 404
        except HTTPError as e:
            return jsonify({"error": str(e)}), response.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    elif op == 'gatcha_receive':
        # Recupera i parametri dal JSON del client
        data = request.get_json()
        user_id = data.get('user_id')
        gatcha_id = data.get('gatcha_id')

        # Controlla che tutti i parametri siano presenti
        if not all([user_id, gatcha_id]):
            return jsonify({"error": "Missing required parameters"}), 400

        # Costruisce l'URL per il servizio auction
        url = f'{AUCTION_BASE_URL}/gatcha_receive'

        try:
            # Invio della richiesta POST al servizio auction
            response = requests.post(url, json=data)
            response.raise_for_status()
            return jsonify(response.json())  # Wrappa la risposta in jsonify
        except ConnectionError:
            return jsonify({"error": "Auction Service is down"}), 404
        except HTTPError as e:
            return jsonify({"error": str(e)}), response.status_code
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    # Caso non gestito
    return jsonify({"error": "Unhandled operation"}), 500

@app.route('/gacha_roll/<op>', methods=['POST'])
def gacha_roll(op):
    if op != 'gacharoll':
        return make_response(f'Invalid operation {op}'),400
    data = request.get_json()
    #Dati che arrivano al gateway da un form lato client
    username = data.get('username')
    level = data.get('level')
    url = GACHAROLL_URL
    params = { 
        'username' : username,
        'level' : level
        }
    try:
        x = requests.post(url, json=params)
        x.raise_for_status()
        res = x.json()
        return res
    except ConnectionError:
        try:
            x = requests.post(url, json=params)
            x.raise_for_status()
            res = x.json()
            return res
        except ConnectionError:
            return make_response("Gacha Roll Service is down\n",404)
        except HTTPError:
            return make_response(x.content, x.status_code)
        return res
    except HTTPError:
        return make_response(x.content, x.status_code)
    
@app.route('/image_gacha/uploads/<name>', methods=['GET'])
def gacha_image(name):
    url = GACHA_IMAGE_URL + name
    file_extension = os.path.splitext(name)[1][1:]  # Rimuovi il punto e ottieni l'estensione
    # Determina il tipo MIME in base all'estensione
    mime_type = get_mime_type(file_extension)
    try:
        x = requests.get(url)
        if x.status_code == 200:
            # Create an in-memory file object
            file = BytesIO(x.content)
            
            # Return the file to the client (forward the file)
            return send_file(file, mimetype=mime_type)
        
        else:
            # Return a 404 if the file was not found in the service
            return jsonify({"error": "File not found"}), 404
    
    except ConnectionError as e:
        try:
            x = requests.get(url)
            if x.status_code == 200:
                # Create an in-memory file object
                file = BytesIO(x.content)
                
                # Return the file to the client (forward the file)
                return send_file(file, mimetype=mime_type)
            else:
                # Return a 404 if the file was not found in the service
                return jsonify({"error": "File not found"}), 404
        
        except ConnectionError as e:
            # Handle any error that occurs while contacting the service
            return jsonify({"error": str(e)}), 500
        except HTTPError:
            return make_response(x.content, x.status_code)
    except HTTPError:
        return make_response(x.content, x.status_code)
    
@app.route('/image_profile/uploads/<name>', methods=['GET'])
def profile_image(name):
    url = PROFILE_IMAGE_URL + name
    file_extension = os.path.splitext(name)[1][1:]  # Rimuovi il punto e ottieni l'estensione
    # Determina il tipo MIME in base all'estensione
    mime_type = get_mime_type(file_extension)
    try:
        x = requests.get(url)
        if x.status_code == 200:
            # Create an in-memory file object
            file = BytesIO(x.content)
            
            # Return the file to the client (forward the file)
            return send_file(file, mimetype=mime_type)
        
        else:
            # Return a 404 if the file was not found in the service
            return jsonify({"error": "File not found"}), 404
    
    except ConnectionError as e:
        try:
            x = requests.get(url)
            if x.status_code == 200:
                # Create an in-memory file object
                file = BytesIO(x.content)
                
                # Return the file to the client (forward the file)
                return send_file(file, mimetype=mime_type)
            else:
                # Return a 404 if the file was not found in the service
                return jsonify({"error": "File not found"}), 404
        
        except ConnectionError as e:
            # Handle any error that occurs while contacting the service
            return jsonify({"error": str(e)}), 500
        except HTTPError:
            return make_response(x.content, x.status_code)
    except HTTPError:
        return make_response(x.content, x.status_code)
    
@app.route('/payment_service/buycurrency', methods=['POST'])
def buycurrency():
    username = request.form.get('username')
    amount = request.form.get('amount')
    method = request.form.get('method')

    url = BUYCURRENCY_URL
    params ={
        'username' : username,
        'amount' : amount,
        'method' : method
    }
    try:
        x = requests.post(url, json=params)
        x.raise_for_status()
        res = x.json()
        return res
    except ConnectionError:
        try:
            x = requests.post(url, json=params)
            x.raise_for_status()
            res = x.json()
            return res
        except ConnectionError:
            return make_response("Gacha Roll Service is down\n",404)
        except HTTPError:
            return make_response(x.content, x.status_code)
        return res
    except HTTPError:
        return make_response(x.content, x.status_code)
    