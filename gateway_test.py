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

print("Updating a gacha ...")

url = 'http://localhost:5001/gachasystem_service/update_gacha'

data = {
            "gacha_name": "Trial gacha Doge-meme.jpg",
            "rarity": 'legendary',
            "description": "This is a rare gacha for Doge-meme.jpg."
        }

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

# Invia la richiesta POST
response = requests.patch(url, data=data)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')


print("Seeing the collection ...")

url = 'http://localhost:5001/gachasystem_service/get_gacha_collection'

data = {
        }

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

# Invia la richiesta POST
response = requests.get(url, data=data)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')

print("Deleting a gacha ...")

url = 'http://localhost:5001/gachasystem_service/delete_gacha'

data = {
            "gacha_name": "Trial gacha Doge-meme.jpg",
        }

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

# Invia la richiesta POST
response = requests.delete(url, data=data)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')

print("Seeing the collection ...")

url = 'http://localhost:5001/gachasystem_service/get_gacha_collection'

data = {
        }

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

# Invia la richiesta POST
response = requests.get(url, data=data)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')
