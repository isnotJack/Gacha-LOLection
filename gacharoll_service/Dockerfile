# Usa un'immagine di base Python
FROM python:3.9

# Imposta la cartella di lavoro all'interno del container
WORKDIR /app

# Copia il file requirements.txt e installa le dipendenze
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il codice sorgente del servizio
# COPY . .

# Imposta le variabili d'ambiente
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5007
ENV FLASK_ENV=development

# Espone la porta sulla quale l'app Flask sarà in esecuzione
EXPOSE 5007

# Comando per eseguire l'app Flask
CMD ["flask", "run"]
