import requests

# # URL a cui inviare la richiesta POST
# url = 'http://172.19.0.3:5001/newBalance'
url = 'http://localhost:5001/auth_service/signup'
# Dati da inviare nella richiesta POST (puoi passare dei dati come un dizionario)

data = {
    'username' : 'user1',
    'password' : '1234',
    'email':'coglione@gmail.com'
}
# Invia la richiesta POST
response = requests.post(url, data)

# # Supponiamo che tu abbia il token JWT salvato dopo il login
# jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczMTY4MTYzNCwianRpIjoiZDE5OTU3NzYtZTkzZi00OWQ5LWI1N2QtZWIyMjRjNWI0NmNhIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJ1c2VybmFtZSI6InVzZXIxIiwicm9sZSI6InVzZXIifSwibmJmIjoxNzMxNjgxNjM0LCJleHAiOjE3MzE2ODI1MzR9.kCAlZs4RRt7bio5hOHH0MDU5KziJ4hZs3iN9I_Zg6l8"
#  # Header con il token JWT
# headers = {
#     'Authorization': f'Bearer {jwt_token}'
# }

#  # Invia la richiesta DELETE per effettuare il logout
# response = requests.get(url, data,headers=headers)

# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')
