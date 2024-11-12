import requests

# # URL a cui inviare la richiesta POST
# url = 'http://172.19.0.3:5001/newBalance'
url = 'http://172.19.0.3:5001/viewTrans'
# Dati da inviare nella richiesta POST (puoi passare dei dati come un dizionario)
# data = {
#     'payer_us': 'user1',
#     'receiver_us': 'user2',
#     'amount': 15
#     }
# data = {
#     'username' : 'user1',
#     'amount' : 100,
#     'method' : 'card'
# }
data = {
    'username' : 'user1'
}
# Invia la richiesta POST
response = requests.get(url, data)

# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')
