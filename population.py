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


# Imposta il percorso della cartella contenente le immagini
images_folder = "./meme images"
url = "http://localhost:5009/gachasystem_service/add_gacha"
# url = "http://localhost:5004/add_gacha"

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
        response = requests.post(url, files=files, data=data)
        
        # Mostra l'esito della richiesta
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}\n")




# # Supponiamo che tu abbia il token JWT salvato dopo il login
# jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczMTg1NTA3NCwianRpIjoiNmFkYmYzZTAtM2U1YS00YzQ2LWI2YzMtOTM3ZGYxZWEwMjg2IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6eyJ1c2VybmFtZSI6InVzZXIxIiwicm9sZSI6InVzZXIifSwibmJmIjoxNzMxODU1MDc0LCJleHAiOjE3MzE4NTU5NzR9.CFJAzYw1dvviXkbqcDuJ1aHkDJtNWpySC1GlOIeT4vM"
#  Header con il token JWT
# headers = {
#     'Authorization': f'Bearer {jwt_token}'
# }

# #  # Invia la richiesta DELETE per effettuare il logout
# response = requests.patch(url, data,headers=headers)

# Verifica la risposta
if response.status_code == 200:
    print('Successo:', response.json())  # Se la risposta è in formato JSON
else:
    print(f'Errore {response.status_code}: {response.text}')
