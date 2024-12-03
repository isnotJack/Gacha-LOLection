# Usa un'immagine Python come base
FROM python:3.9

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file necessari
COPY . /app

# Copia le immagini dei meme
COPY meme_images /app/static/uploads

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade setuptools
RUN apt-get update && apt-get install -y postgresql-15
RUN pip install --upgrade pip

# Imposta le variabili d'ambiente
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5004
ENV FLASK_ENV=development  

# Espone la porta dell'applicazione
EXPOSE 5004

# Comando per avviare il servizio
CMD ["flask", "run", "--host=0.0.0.0", "--port=5004", "--cert=/app/gachasystem_cert.pem", "--key=/app/gachasystem_key.pem"]
