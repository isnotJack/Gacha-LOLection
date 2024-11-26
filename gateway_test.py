import os
import requests

url = 'http://localhost:5001/payment_service/buycurrency'

data1 = {
    'username' : 'user1',
    'amount':'100',
    'payment_method' : 'card'
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

# print("Updating a gacha ...")

# url = 'http://localhost:5001/gachasystem_service/update_gacha'

# data = {
#             "gacha_name": "Trial gacha Doge-meme.jpg",
#             "rarity": 'legendary',
#             "description": "This is a rare gacha for Doge-meme.jpg."
#         }

# # data2 = {
# #     'username' : 'user2',
# #     'password' : '1234'
# #     ,'email' : 'user2@gmail.com'
# # }

# # data3 = {
# #     'username' : 'user3',
# #     'password' : '1234'
# #     ,'email' : 'user3@gmail.com'
# # }

# # Invia la richiesta POST
# response = requests.patch(url, data=data)
# # Verifica la risposta
# if response.status_code == 200:
#     print('Successo:', response.json())  # Se la risposta è in formato JSON
# else:
#     print(f'Errore {response.status_code}: {response.text}')


# print("Seeing the collection ...")

# url = 'http://localhost:5001/gachasystem_service/get_gacha_collection'

# data = {
#         }

# # data2 = {
# #     'username' : 'user2',
# #     'password' : '1234'
# #     ,'email' : 'user2@gmail.com'
# # }

# # data3 = {
# #     'username' : 'user3',
# #     'password' : '1234'
# #     ,'email' : 'user3@gmail.com'
# # }

# # Invia la richiesta POST
# response = requests.get(url, data=data)
# # Verifica la risposta
# if response.status_code == 200:
#     print('Successo:', response.json())  # Se la risposta è in formato JSON
# else:
#     print(f'Errore {response.status_code}: {response.text}')

# print("Deleting a gacha ...")

# url = 'http://localhost:5001/gachasystem_service/delete_gacha'

# data = {
#             "gacha_name": "Trial gacha Doge-meme.jpg",
#         }

# # data2 = {
# #     'username' : 'user2',
# #     'password' : '1234'
# #     ,'email' : 'user2@gmail.com'
# # }

# # data3 = {
# #     'username' : 'user3',
# #     'password' : '1234'
# #     ,'email' : 'user3@gmail.com'
# # }

# # Invia la richiesta POST
# response = requests.delete(url, data=data)
# # Verifica la risposta
# if response.status_code == 200:
#     print('Successo:', response.json())  # Se la risposta è in formato JSON
# else:
#     print(f'Errore {response.status_code}: {response.text}')

# print("Seeing the collection ...")

# url = 'http://localhost:5001/gachasystem_service/get_gacha_collection'

# data = {
#         }

# # data2 = {
# #     'username' : 'user2',
# #     'password' : '1234'
# #     ,'email' : 'user2@gmail.com'
# # }

# # data3 = {
# #     'username' : 'user3',
# #     'password' : '1234'
# #     ,'email' : 'user3@gmail.com'
# # }

# # Invia la richiesta POST
# response = requests.get(url, data=data)
# # Verifica la risposta
# if response.status_code == 200:
#     print('Successo:', response.json())  # Se la risposta è in formato JSON
# else:
#     print(f'Errore {response.status_code}: {response.text}')


# Login
try:
    url = 'http://localhost:5001/auth_service/login'
    params = {
        'username': 'user1',
        'password': '1234'
    }

    # Effettua la richiesta POST per il login
    response = requests.post(url, data=params)

    if response.status_code == 200:
        print('Login avvenuto con successo.')
        # Recupera il token JWT
        data= response.json()
        jwt_token = data.get('access_token')
        if jwt_token:
            print(f'Token JWT ricevuto: {jwt_token}')
        else:
            print(f'Errore: Token JWT non ricevuto nel login.{data}')
            exit(1)
    else:
        print(f'Errore {response.status_code} durante il login: {response.text}')
        exit(1)
except requests.ConnectionError as e:
    print(f'Errore di connessione durante il login: {e}')
    exit(1)
except Exception as e:
    print(f'Errore generico durante il login: {e}')
    exit(1)

print('Sending request to roll')
url = 'http://localhost:5007/gacharoll'
 
data1 = {
    'username' : 'user1',
    'level':'medium'
}
 
headers = {
    'Authorization' : f"Bearer {jwt_token}"
}
# Invia la richiesta POST
response = requests.post(url, json=data1, headers=headers)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')


# # Logout
# try:
#     url = 'http://localhost:5001/auth_service/logout'
#     headers = {
#         'Authorization': f'Bearer {jwt_token}'  # Aggiungi il token JWT nell'header
#     }

#     # Effettua la richiesta DELETE per il logout
#     response = requests.delete(url, headers=headers)

#     if response.status_code == 200:
#         print('Logout avvenuto con successo.')
#     else:
#         print(f'Errore {response.status_code} durante il logout: {response.text}')
# except requests.ConnectionError as e:
#     print(f'Errore di connessione durante il logout: {e}')
# except Exception as e:
#     print(f'Errore generico durante il logout: {e}')

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
