import requests
import os

#SCRIPT DI POPOLAZIONE
#REGISTRO 3 UTENTI
url = 'http://localhost:5001/auth_service/signup'

admin_url = 'http://localhost:5009/auth_service/signup'
data={
    'username' : 'system',
    'password' : '1234'
    ,'email' : 'system@gmail.com'
}

data1 = {
    'username' : 'user1',
    'password' : '1234'
    ,'email' : 'user1@gmail.com'
}

data2 = {
    'username' : 'user2',
    'password' : '1234'
    ,'email' : 'user2@gmail.com'
}

data3 = {
    'username' : 'user3',
    'password' : '1234'
    ,'email' : 'user3@gmail.com'
}

# Invia la richiesta POST
response = requests.post(admin_url, data=data)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')

# Invia la richiesta POST
response = requests.post(url, data=data1)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')

response = requests.post(url, data=data2)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')

response = requests.post(url, data=data3)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')

    # LOGIN ADMIN #

admin_url = 'http://localhost:5009/auth_service/login'
data={
    'username' : 'system',
    'password' : '1234'
    }
response = requests.post(admin_url, data=data)
# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')
token = response.json()

admin_token = token.get('access_token')
headers = {
    'Authorization' : f'Bearer {admin_token}'
}

admin_ref_token = token.get('refresh_token')
ref_headers = {
    'Authorization' : f'Bearer {admin_ref_token}'
}


# Imposta il percorso della cartella contenente le immagini
images_folder = "./meme images"
url = "http://localhost:5009/gachasystem_service/add_gacha"

count = 0
rarity = ['common', 'rare', 'legendary' ]
# Itera sui file della cartella
for filename in os.listdir(images_folder):
    # Costruisci il percorso completo del file
    file_path = os.path.join(images_folder, filename)
    
    # Verifica che sia un file e abbia un'estensione immagine valida
    if os.path.isfile(file_path) and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        print(f"Inserisco {filename}...")
        
        # Prepara i dati e i file per la richiesta POST
        files = {
            "image": open(file_path, "rb")
        }
        data = {
            "gacha_name": f"Trial gacha {filename}",
            "rarity": rarity[count],
            "description": f"This is a rare gacha for {filename}."
        }
        count = (count +1) % 3
        # Invia la richiesta POST
        response = requests.post(url, files=files, data=data, headers=headers)
        
        # Mostra l'esito della richiesta
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}\n")
    
try:
    url = 'http://localhost:5009/auth_service/logout'
    
    # Effettua la richiesta DELETE per il logout
    response = requests.delete(url, headers=ref_headers)

    if response.status_code == 200:
        print('Logout avvenuto con successo.')
    else:
        print(f'Errore {response.status_code} durante il logout: {response.text}')
except requests.ConnectionError as e:
    print(f'Errore di connessione durante il logout: {e}')
except Exception as e:
    print(f'Errore generico durante il logout: {e}')


