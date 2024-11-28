import os
import requests


# LOGIN DI DUE UTENTI E DELL'ADMIN #
print("Login of 2 client and 1 admin \n")
url = 'http://localhost:5001/auth_service/login'
admin_url = 'http://localhost:5009/auth_service/login'
admin={
    'username' : 'system',
    'password' : '1234'
}

user1 = {
    'username' : 'user1',
    'password' : '1234'
}

user2 = {
    'username' : 'user2',
    'password' : '1234'
}


response = requests.post(admin_url, data=admin)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')
token = response.json()

admin_ref_token = token.get('refresh_token')
a_ref_headers = {
    'Authorization' : f'Bearer {admin_ref_token}'
}


admin_token = token.get('access_token')
aheaders = {
    'Authorization' : f'Bearer {admin_token}'
}

response = requests.post(url, data=user1)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')
token = response.json()

user1_token = token.get('access_token')
headers1 = {
    'Authorization' : f'Bearer {user1_token}'
}
user1_ref_token = token.get('refresh_token')
user1_ref_headers = {
    'Authorization' : f'Bearer {user1_ref_token}'
}

response = requests.post(url, data=user2)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')
token = response.json()

user2_token = token.get('access_token')
headers2 = {
    'Authorization' : f'Bearer {user2_token}'
}
user2_ref_token = token.get('refresh_token')
user2_ref_headers = {
    'Authorization' : f'Bearer {user2_ref_token}'
}


print("2 clients buy currency \n")
url = 'http://localhost:5001/payment_service/buycurrency'

data1 = {
    'username' : 'user1',
    'amount':'100',
    'payment_method' : 'card'
}

data2 = {
    'username' : 'user2',
    'amount':'100',
    'payment_method' : 'card'
}

# Invia la richiesta POST
response = requests.post(url, data=data1, headers=headers1)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')

# Invia la richiesta POST
response = requests.post(url, data=data2, headers=headers2)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')

print("Admin tries to update a gacha")

url = 'http://localhost:5009/gachasystem_service/update_gacha'

data = {
            "gacha_name": "Trial gacha Doge-meme.jpg",
            "rarity": 'legendary',
            "description": "This is a rare gacha for Doge-meme.jpg."
        }

# Invia la richiesta POST
response = requests.patch(url, data=data, headers=aheaders)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')


print("Two clients roll a gacha")


url = 'http://localhost:5001/gacha_roll/gacharoll'

data1 = {
        'username' : 'user1',
        'level' : 'premium'
        }
data2 = {
        'username' : 'user2',
        'level' : 'standard'
        }

# Invia la richiesta POST
response = requests.post(url, json=data1, headers=headers1)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')

# Invia la richiesta P
response = requests.post(url, json=data2 , headers=headers2)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')

print("Deleting a gacha")

url = 'http://localhost:5009/gachasystem_service/delete_gacha'
data = {
            "gacha_name": "Trial gacha Doge-meme.jpg",
        }


# Invia la richiesta POST
response = requests.delete(url, data=data, headers=aheaders)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')


print("Seeing the collection of both")

url1 = 'http://localhost:5001/profile_setting/retrieve_gachacollection?username=user1'
url2 = 'http://localhost:5001/profile_setting/retrieve_gachacollection?username=user2'
# data1 = {
#         'username' : 'user1'
#         }
# data2 = {
#         'username' : 'user2'
#         }


# Invia la richiesta POST
response = requests.get(url1, headers=headers1)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')


# Invia la richiesta POST
response = requests.get(url2, headers=headers2)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')

#NEW TOKEN 
url = 'http://localhost:5001/auth_service/newToken'
response = requests.get(url, headers=user1_ref_headers)

if response.status_code == 200:
    print(f'Nuovo token ottenuto. {response.json()}')
else:
    print(f'Errore {response.status_code} durante new token: {response.text}')


# Logout

url = 'http://localhost:5001/auth_service/logout'

# Effettua la richiesta DELETE per il logout
response = requests.delete(url, headers=user1_ref_headers)

if response.status_code == 200:
    print('Logout avvenuto con successo.')
else:
    print(f'Errore {response.status_code} durante il logout: {response.text}')


# #Delete
# # Logout
# try:
#     url = 'http://localhost:5001/auth_service/delete'
#     params= {
#         'username' : 'user1',
#         'password' : '1234'
#     }

#     # Effettua la richiesta DELETE per il logout
#     response = requests.delete(url, data=params)

#     if response.status_code == 200:
#         print('Delete avvenuto con successo.')
#     else:
#         print(f'Errore {response.status_code} durante il logout: {response.text}')
# except requests.ConnectionError as e:
#     print(f'Errore di connessione durante il logout: {e}')
# except Exception as e:
#     print(f'Errore generico durante il logout: {e}')
