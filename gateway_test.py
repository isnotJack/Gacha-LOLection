import os
import requests

url = 'http://localhost:5001/payment_service/buycurrency'

data1 = {
    'username' : 'user1',
    'amount':'100',
    'method' : 'card'
}

# data2 = {
#     'username' : 'user2',
#     'password' : '1234'
#     ,'email' : 'user2@gmail.com'
# }

# data3 = {
#     'username' : 'user3',
#     'password' : '1234'
#     ,'email' : 'user3@gmail.com'
# }

# Invia la richiesta POST
response = requests.post(url, data=data1)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')


print('Sending request to roll')
url = 'http://localhost:5001/gacha_roll/gacharoll'

data1 = {
    'username' : 'user1',
    'level':'medium'
}

# data2 = {
#     'username' : 'user2',
#     'password' : '1234'
#     ,'email' : 'user2@gmail.com'
# }

# data3 = {
#     'username' : 'user3',
#     'password' : '1234'
#     ,'email' : 'user3@gmail.com'
# }

# Invia la richiesta POST
response = requests.post(url, json=data1)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')