import requests, time

from flask import Flask, request, make_response 
from requests.exceptions import ConnectionError, HTTPError
from werkzeug.exceptions import NotFound


ALLOWED_AUTH_OP ={'signup', 'login', 'logout', 'delete'}
SINGUP_URL = 'http://auth_service:5002/signup'
LOGIN_URL = 'http://auth_service:5002/login'
LOGOUT_URL = 'http://auth_service:5002/logout'
DELETE_URL = 'http://auth_service:5002/delete'

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


    