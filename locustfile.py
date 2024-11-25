from locust import HttpUser, task, between
import random
import string
import os

class GachaUser(HttpUser):
    """
    Simulation of a user that registers, logs in and then uses the system.
    """
    wait_time = between(5, 15)

    def on_start(self):
        self.generate_random_credentials()
        self.signup()
        self.login()
    
    def generate_random_credentials(self):
        self.username = f"user{random.randint(0, 9999)}"
        self.email = f"{self.username}@test.com"
        password_length = 10  # Lunghezza della password
        characters = string.ascii_letters + string.digits + string.punctuation
        self.password = ''.join(random.choice(characters) for i in range(password_length))

    def signup(self):           
        payload = {
            "username": self.username,
            "password": self.password,
            "email": self.email
        }
        signup_response = self.client.post("/auth_service/signup", json=payload, name="Signup Endpoint")
        if signup_response != 200:
            self.stop()

    def login(self):
        payload = {
            "username": self.username,
            "password": self.password
        }
        login_response = self.client.post("/auth_service/login", json=payload, name="Login Endpoint")
        if login_response != 200:
            self.stop()

    @task(1)
    def modify_profile (self):
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

                self.client.patch("/profile_setting/modify_profile", data=params, files=files)
        else:
            print(f"error: file {image_path} not found.")

    @task(1)
    def check_profile(self):
        params = {
            "username": self.username
        }
        self.client.get("/profile_setting/checkprofile", params=params)

    @task(2)
    def gacha_roll(self):
        level = random.choice(['standard', 'medium', 'premium'])
        gacha_payload = {
            "username": self.username,
            "level": level 
        }
        self.client.get("/gacha_roll/gacharoll", gacha_payload)

    @task(2)
    def create_auction(self):
        retrieve_response = self.client.get("/profile_setting/retrieve_gachacollection")
        
    
    def on_stop(self):
        # logout
        self.client.get("/auth_service/logout", name="Logout Endpoint")