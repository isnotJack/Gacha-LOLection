from locust import HttpUser, task, between
import random
import string
import os

class GachaUser(HttpUser):
    """
    Simulation of a user that registers, logs in and then uses the system.
    """
    wait_time = between(5, 15)

    def on_start(self):     # metodo chiamato automaticamente all'avvio di ogni utente simulato
        self.generate_random_credentials()
        self.signup()
        self.login()
        self.buy_currency() # acquisto di monete subito dopo il login
    
    def generate_random_credentials(self):
        # genera credenziali casuali in modo che ogni utente simulato abbia un accout unico
        self.username = f"user{random.randint(0, 9999)}"
        self.email = f"{self.username}@gmail.com"
        password_length = 10  # Lunghezza della password
        characters = string.ascii_letters + string.digits + string.punctuation
        self.password = ''.join(random.choice(characters) for i in range(password_length))

    def signup(self):           
        payload = {
            "username": self.username,
            "password": self.password,
            "email": self.email
        }
        signup_response = self.client.post("/auth_service/signup", data=payload, verify=False, name="Signup Endpoint")
        if signup_response.status_code != 200:
            print(f"Error during signup: {signup_response.text}")
            self.stop()

    def login(self):
        payload = {
            "username": self.username,
            "password": self.password
        }
        login_response = self.client.post("/auth_service/login", data=payload, verify=False, name="Login Endpoint")
        if login_response.status_code != 200:
            print(f"Error during login: {login_response.text}")
            self.stop()
        else:
            self.jwt_token = login_response.json().get("access_token")

    @task(1)
    def modify_profile_image (self):
        # task che permette di modificare l'immagine del profilo dell'utente
        # Percorso dell'immagine da caricare
        image_path = "./profile_setting/ProfileImages/man1.png"  # Inserisci il percorso dell'immagine

        if os.path.exists(image_path):
            with open(image_path, 'rb') as image_file:
                # Imposta i dati del form
                params = {
                    'username': self.username
                }
                
                # Crea il file immagine per il form
                files = {
                    'image': (image_file.name, image_file, 'image/png')  # Tipo MIME dell'immagine
                }

                headers = {
                    'Authorization': f"Bearer {self.jwt_token}"
                }

                response = self.client.patch("/profile_setting/modify_profile", data=params, files=files, verify=False, headers=headers, name="Modify Profile Image Endpoint")
                if response.status_code != 200:
                    print(f"Error during profile image modification: {response.text}")
        else:
            print(f"error: file {image_path} not found.")

    @task(1)
    def modify_profile_email(self):
        # Task per modificare l'email dell'utente
        random_number = random.randint(0,99)
        new_email = f"{self.username}{random_number}@newdomain.com"  # Nuova email generata dinamicamente

        # Dati da inviare per la modifica del profilo
        payload = {
            'username': self.username,  # Il nome utente rimane invariato
            'field': "email",
            'value': new_email  # Nuova email da impostare
        }

        # Header per l'autenticazione con il token JWT
        headers = {
            'Authorization': f"Bearer {self.jwt_token}"
        }

        # Esegui la richiesta per modificare l'email
        response = self.client.patch("/profile_setting/modify_profile", data=payload, verify=False, headers=headers, name="Modify Profile Email Endpoint")

        if response.status_code != 200:
        #     print(f"Email successfully updated to: {new_email}")
        # else:
            print(f"Failed to update email: {response.text}")

    @task(1)
    def check_profile(self):
        params = {
            "username": self.username
        }
        headers = {
            'Authorization': f"Bearer {self.jwt_token}"
        }
        response = self.client.get("/profile_setting/checkprofile", params=params, verify=False, headers=headers, name="Check Profile Endpoint")
        if response.status_code != 200:
            print(f"Error during profile check: {response.text}")

    @task(1)
    def buy_currency(self):
        """
        This task simulates the purchase of currency
        """
        payload = {
            "username": self.username,          # Usa il nome utente generato
            "amount": random.randint(1, 100),   # La quantità di monete da acquistare (ad esempio, tra 1 e 100)
            "payment_method": "card"            # Supponiamo che il metodo di pagamento sia "card"
        }
        headers = {
            "Authorization": f"Bearer {self.jwt_token}"
        }

        response = self.client.post("/payment_service/buycurrency", data=payload, verify=False, headers=headers, name="Buy Currency Endpoint")
        if response.status_code != 200:
            print(f"Error during currency purchase: {response.text}")

    @task(1)
    def roll(self):
        """
        This task simulates performing a roll in the game.
        """
        level = random.choice(['standard', 'medium', 'premium'])  # Seleziona un livello casuale per il roll
        payload = {
            "username": self.username,
            "level": level
        }
        headers = {
            "Authorization": f"Bearer {self.jwt_token}"
        }
        response = self.client.post("/gacha_roll/gacharoll", json=payload, verify=False, headers=headers, name="Roll Endpoint")
        if response.status_code != 200:
            print(f"Error during gacha roll: {response.text}")

    @task(1)
    def create_auction(self):
        # 1. Recupera la lista dei gacha posseduti dall'utente
        headers = {
            'Authorization': f'Bearer {self.jwt_token}'  # Usa il token per l'autenticazione
        }
        params = {
            'username': self.username
        }
        response = self.client.get("/profile_setting/retrieve_gachacollection", params=params, verify=False, headers=headers, name="Retrieve Gacha Collection Endpoint")
        
        if response.status_code == 200:
            gacha_collection = response.json()  # Qui prendiamo la lista direttamente, senza cercare 'gacha_collection'
            if gacha_collection:
                # 2. Scegli un gacha casuale dalla lista
                selected_gacha = random.choice(gacha_collection)
                gacha_name = selected_gacha.get('gacha_name')
                
                # 3. Crea l'asta con il gacha scelto
                auction_data = {
                    'seller_username': self.username,
                    'gacha_name': gacha_name,
                    'basePrice': 10,  
                    'endDate': '2024-12-31T23:59:59' 
                }
                
                # Chiamata alla creazione dell'asta
                auction_response = self.client.post("/auction_service/create", json=auction_data, verify=False, headers=headers, name="Create Auction Endpoint")
                if auction_response.status_code == 200:
                    print(f"Auction created successfully for gacha '{gacha_name}'")
                else:
                    print(f"Failed to create auction: {auction_response.text}")
            else:
                print("No gacha found in the collection.")
        else:
            print(f"Failed to retrieve gacha collection: {response.text}")
        
    @task(1)
    def bid_auction(self):
        # Prima otteniamo la lista di tutte le aste attive
        headers = {
            'Authorization': f"Bearer {self.jwt_token}"  # Autenticazione tramite il token
        }

        # Esegui la richiesta per ottenere tutte le aste attive
        response = self.client.get("/auction_service/see", verify=False, headers=headers, name="See Active Auctions Endpoint")

        if response.status_code == 200:
            active_auctions = response.json()  # Lista delle aste attive
            if active_auctions:
                # Scegliamo un'asta casuale dalla lista
                selected_auction = random.choice(active_auctions)
                auction_id = selected_auction.get('auction_id')
                gacha_name = selected_auction.get('gacha_name')
                #base_price = selected_auction.get('basePrice')
                current_bid = selected_auction.get('current_bid')

                # Print per debug
                print(f"Selected auction ID: {auction_id}, Gacha Name: {gacha_name}, Current Bid: {current_bid}")

                # Generiamo una bid (offerta) casuale che sia maggiore dell'offerta attuale
                bid_amount = current_bid + random.randint(1, 10)  # Offriamo una somma maggiore dell'offerta attuale

                # Chiamata per ottenere il proprio currency e verificare se si hanno sufficienti soldi DA FARE

                # Dati per la bid
                bid_data = {
                    "username": self.username,
                    "auction_id": auction_id,
                    "amount": bid_amount
                }

                # Chiamata per fare un bid sull'asta selezionata
                bid_response = self.client.patch("/auction_service/bid", params=bid_data, verify=False, headers=headers, name="Bid on Auction Endpoint")

                # Verifica che la risposta della bid sia positiva
                if bid_response.status_code != 200:
                #     print(f"Bid placed successfully on auction {auction_id} for {bid_amount} coins")
                # else:
                    print(f"Failed to place bid on auction {auction_id}: {bid_response.text}")
            else:
                print("No active auctions found.")
        else:
            print(f"Failed to retrieve active auctions: {response.text}")

    def on_stop(self):
        # logout
        headers = {
                "Authorization": f"Bearer {self.jwt_token}"
        }
        response = self.client.delete("/auth_service/logout", verify=False, headers=headers, name="Logout Endpoint")
        if response.status_code != 200:
            print(f"Error during logout: {response.text}")