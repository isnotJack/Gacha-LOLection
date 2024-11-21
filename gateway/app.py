import requests, time
import os
from flask import Flask, request, make_response, jsonify, send_file
from requests.exceptions import ConnectionError, HTTPError
from werkzeug.exceptions import NotFound
from io import BytesIO


ALLOWED_GACHA_SYS_OP ={'add_gacha', 'delete_gacha', 'update_gacha', 'get_gacha_collection'}
ADD_URL = 'http://gachasystem:5004/add_gacha'
DELETE_GACHA_URL = 'http://gachasystem:5004/delete_gacha'
UPDATE_GACHA_URL = 'http://gachasystem:5004/update_gacha'
GET_GACHA_COLL_URL = 'http://gachasystem:5004/get_gacha_collection'
GACHA_IMAGE_URL = 'http://gachasystem:5004/uploads/'

ALLOWED_AUTH_OP ={'signup', 'login', 'logout', 'delete'}
SINGUP_URL = 'http://auth_service:5002/signup'
LOGIN_URL = 'http://auth_service:5002/login'
LOGOUT_URL = 'http://auth_service:5002/logout'
DELETE_URL = 'http://auth_service:5002/delete'

ALLOWED_PROF_OP ={'modify_profile','checkprofile', 'retrieve_gachacollection', 'info_gachacollection'}
MODIFY_URL = 'http://profile_setting:5003/modify_profile'
CHECK_URL = 'http://profile_setting:5003/checkprofile'
RETRIEVE_URL = 'http://profile_setting:5003/retrieve_gachacollection'
INFO_URL = 'http://profile_setting:5003/info_gachacollection'

ALLOWED_AUCTION_OP = {'see', 'create', 'modify', 'bid','gacha_receive', 'auction_lost', 'auction_terminated'} 
AUCTION_BASE_URL = 'http://auction_service:5008'
SEE_AUCTION_URL = f'{AUCTION_BASE_URL}/see'
CREATE_AUCTION_URL = f'{AUCTION_BASE_URL}/create'
MODIFY_AUCTION_URL = f'{AUCTION_BASE_URL}/modify'
BID_AUCTION_URL = f'{AUCTION_BASE_URL}/bid'
GACHA_RECEIVE_URL = f'{AUCTION_BASE_URL}/gacha_receive'
AUCTION_LOST_URL = f'{AUCTION_BASE_URL}/auction_lost'

GACHAROLL_URL = 'http://gacha_roll:5007/gacharoll'

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
            x = requests.post(url, json=params, timeout=10)
        elif (op == 'logout'):
            x = requests.delete(url, headers=headers, timeout=10)
        else:
            x = requests.delete(url, json=params, timeout=10)
        x.raise_for_status()
        res = x.json()
        return res
    except requests.exceptions.Timeout:
        return jsonify({"Error": "Time out expired"}), 408
    except ConnectionError:
        try:
            if(op == 'login' or op=='signup'):
                x = requests.post(url, json=params, timeout=10)
            elif (op == 'logout'):
                x = requests.delete(url, headers=headers, timeout=10)
            else:
                x = requests.delete(url, json=params, timeout=10)
            x.raise_for_status()
            res = x.json()
            return res
        except requests.exceptions.Timeout:
            return jsonify({"Error": "Time out expired"}), 408
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
    if op == 'modify_profile':
        #Dati che arrivano al gateway da un form lato client
        username = request.form.get('username')
        value = request.form.get('value')
        field = request.form.get('field')
        file = request.files['image']
        files = {'image': (file.filename, file.stream, file.mimetype)}
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
        gacha_id = request.args.get('gacha_id')
        url = RETRIEVE_URL + f"?username={username}&gacha_id={gacha_id}"
        jwt_token = request.headers.get('Authorization')  # Supponiamo che il token JWT sia passato nei headers come 'Authorization'
        headers = {
            'Authorization': jwt_token  # Usa il token JWT ricevuto nell'header della richiesta
        }
    try:
        if(op == 'modify_profile'):
            x = requests.patch(url, data=params, files=files, timeout=10)
        else:
            x = requests.get(url, headers=headers, timeout=10)
        x.raise_for_status()
        res = x.json()
        return res
    except requests.exceptions.Timeout:
        return jsonify({"Error": "Time out expired"}), 408
    except ConnectionError:
        try:
            if(op == 'modify_profile'):
                x = requests.patch(url, data=params, files=files, timeout=10)
            else:
                x = requests.get(url, headers=headers, timeout=10)
            x.raise_for_status()
            res = x.json()
            return res
        except requests.exceptions.Timeout:
            return jsonify({"Error": "Time out expired"}), 408
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
            seller_username = data.get('seller_username')  # Corretto da seller_id a seller_username
            gacha_name = data.get('gacha_name')  # Corretto da gacha_id a gacha_name
            base_price = data.get('basePrice')
            end_date = data.get('endDate')

            # Verifica che tutti i parametri richiesti siano presenti
            if not all([seller_username, gacha_name, base_price, end_date]):
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
        seller_username = data.get('seller_username')  # Corretto da seller_id a seller_username
        gacha_name = data.get('gacha_name')         # Corretto da gacha_id a gacha_name
        base_price = data.get('basePrice')
        end_date = data.get('endDate')

        # Controlla che auction_id sia presente
        if not auction_id:
            return jsonify({"error": "Auction ID is required"}), 400

        # Costruisce l'URL con i parametri come query string
        url = f'{MODIFY_AUCTION_URL}?auction_id={auction_id}'
        if seller_username:
            url += f'&seller_username={seller_username}'
        if gacha_name:
            url += f'&gacha_name={gacha_name}'
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


    # Operazione "bid"
    elif op == 'bid':
        # Recupera i parametri dalla query string
        username = request.args.get('username')
        auction_id = request.args.get('auction_id')
        new_bid = request.args.get('newBid', type=float)

        # Verifica che tutti i parametri richiesti siano presenti
        if not all([username, auction_id, new_bid]):
            return jsonify({"error": "Missing required parameters"}), 400

        # Costruisce l'URL con i parametri della query string
        url = f'{AUCTION_BASE_URL}/bid?username={username}&auction_id={auction_id}&newBid={new_bid}'

        try:
            # Effettua la richiesta PATCH all’Auction Service
            response = requests.patch(url)
            response.raise_for_status()
            return jsonify(response.json())  # Wrappa la risposta in jsonify
        except requests.ConnectionError:
            return jsonify({"error": "Auction Service is down"}), 404
        except requests.HTTPError as e:
            return jsonify({"error": f"HTTP Error: {str(e)}"}), response.status_code
        except Exception as e:
            return jsonify({"error": f"Unexpected Error: {str(e)}"}), 500

        
        # Operazione "gacha_receive"
    elif op == 'gacha_receive':
        try:
            # Recupera i parametri dal corpo JSON della richiesta
            data = request.get_json()
            auction_id = data.get('auction_id')
            winner_username = data.get('winner_username')
            gacha_name = data.get('gacha_name')

            # Controlla che tutti i parametri richiesti siano presenti
            if not all([auction_id, winner_username, gacha_name]):
                return jsonify({"error": "Missing required parameters"}), 400

            # Effettua la richiesta al servizio Auction
            url = f'{AUCTION_BASE_URL}/gacha_receive'
            response = requests.post(url, json=data)
            response.raise_for_status()
            return jsonify(response.json())  # Wrappa la risposta in jsonify

        except requests.ConnectionError:
            return jsonify({"error": "Auction Service is down"}), 404
        except requests.HTTPError as e:
            return jsonify({"error": f"HTTP Error: {str(e)}"}), response.status_code
        except Exception as e:
            return jsonify({"error": f"Unexpected Error: {str(e)}"}), 500

    # Operazione "auction_lost"
    elif op == 'auction_lost':
        try:
            # Recupera i parametri dal corpo JSON della richiesta
            data = request.get_json()
            auction_id = data.get('auction_id')

            # Controlla che l'ID dell'asta sia presente
            if not auction_id:
                return jsonify({"error": "Missing auction_id"}), 400

            # Effettua la richiesta al servizio Auction
            url = f'{AUCTION_BASE_URL}/auction_lost'
            response = requests.post(url, json=data)
            response.raise_for_status()
            return jsonify(response.json())  # Wrappa la risposta in jsonify

        except requests.ConnectionError:
            return jsonify({"error": "Auction Service is down"}), 404
        except requests.HTTPError as e:
            return jsonify({"error": f"HTTP Error: {str(e)}"}), response.status_code
        except Exception as e:
            return jsonify({"error": f"Unexpected Error: {str(e)}"}), 500
        
        # Operazione "auction_terminated"
    elif op == 'auction_terminated':
        try:
            # Recupera i parametri dal corpo JSON della richiesta
            data = request.get_json()
            auction_id = data.get('auction_id')

            # Verifica che auction_id sia presente
            if not auction_id:
                return jsonify({"error": "Missing auction_id"}), 400

            # Costruisce l'URL per il servizio Auction
            url = f'{AUCTION_BASE_URL}/auction_terminated'

            # Effettua la richiesta al servizio Auction
            response = requests.post(url, json=data)
            response.raise_for_status()
            return jsonify(response.json())  # Wrappa la risposta in jsonify

        except requests.ConnectionError:
            return jsonify({"error": "Auction Service is down"}), 404
        except requests.HTTPError as e:
            return jsonify({"error": f"HTTP Error: {str(e)}"}), response.status_code
        except Exception as e:
            return jsonify({"error": f"Unexpected Error: {str(e)}"}), 500
    


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
    
@app.route('/gachasystem_service/<op>', methods=['POST', 'DELETE', 'PATCH','GET'])
def gachasystem(op):
    if op not in ALLOWED_GACHA_SYS_OP:
        return make_response(f'Invalid operation {op}'),400
    if op == 'add_gacha':
        #Dati che arrivano al gateway da un form lato client
        gacha_name = request.form.get('gacha_name')
        rarity = request.form.get('rarity')
        description = request.form.get('description')
        file = request.files['image']
        files = {'image': (file.filename, file.stream, file.mimetype)}
        url = ADD_URL
        params = { 
            'gacha_name' : gacha_name,
            'rarity' : rarity,
            'description' : description
            }
    elif op =='delete_gacha':
        gacha_name = request.form.get('gacha_name')
        url = DELETE_GACHA_URL
        params={
            'gacha_name': gacha_name
        }
    elif op == 'update_gacha':
        #Dati che arrivano al gateway da un form lato client
        gacha_name = request.form.get('gacha_name')
        rarity = request.form.get('rarity')
        description = request.form.get('description')
        url = UPDATE_GACHA_URL
        params = { 
            'gacha_name' : gacha_name,
            'rarity' : rarity,
            'description' : description
            }
    elif op == 'get_gacha_collection':
        params={}
        url= GET_GACHA_COLL_URL
    try:
        if(op == 'add_gacha'):
            x = requests.post(url, data=params, files=files)
        elif(op == 'delete_gacha'):
            x = requests.delete(url, json=params)
        elif(op == 'update_gacha'):
            x = requests.patch(url, json=params)
        elif(op == 'get_gacha_collection'):
            x = requests.get(url, json=params)
            x.raise_for_status()
            res = x.json()
            return jsonify(res)
        x.raise_for_status()
        res = x.json()
        return res
    except ConnectionError:
        try:
            if(op == 'add_gacha'):
                x = requests.post(url, data=params, files=files)
            elif(op == 'delete_gacha'):
                x = requests.delete(url, json=params)
            elif(op == 'update_gacha'):
                x = requests.patch(url, json=params)
            elif(op == 'get_gacha_collection'):
                x = requests.get(url, json=params)
                x.raise_for_status()
                res = x.json()
                return jsonify(res)
            x.raise_for_status()
            res = x.json()
            return res
        except ConnectionError:
            return make_response("Gacha System Service is down\n",404)
        except HTTPError:
            return make_response(x.content, x.status_code)
        return res
    except HTTPError:
        return make_response(x.content, x.status_code)