import requests
# URL dell'endpoint di logout
logout_url = 'http://localhost:5002/logout'

# Token di autenticazione (può essere un JWT o altro tipo di token)
token = 'yeyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczMjE4MTU4MiwianRpIjoiYzNmZDBlOGUtNjRmNy00ZDU5LWIzNzUtYmQ1ZGViZmMzMTZhIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJ1c2VybmFtZSI6InVzZXIxIiwicm9sZSI6InVzZXIifSwibmJmIjoxNzMyMTgxNTgyLCJleHAiOjE3MzIxODI0ODJ9.XZeBpcQOA-rzdIU0LrQNgWhV4s9AEwdazqr2rS6i6lQ'

# Intestazioni per l'autenticazione, includendo il token
headers = {'Authorization': f'Bearer {token}'}

# Effettuare la richiesta di logout con metodo GET (può essere anche POST a seconda del server)
response = requests.delete(logout_url, headers=headers)

# Controlla lo stato della risposta
if response.status_code == 200:
    print("Logout effettuato con successo!")
else:
    print(f"Errore nel logout: {response.status_code}")
