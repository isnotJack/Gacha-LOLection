FROM python:3.9

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade setuptools
RUN apt-get update && apt-get install -y postgresql-15
RUN pip install --upgrade pip


ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5008
ENV FLASK_ENV=development

EXPOSE 5008
CMD ["flask", "run", "--host=0.0.0.0", "--port=5008", "--cert=/app/auction_cert.pem", "--key=/app/auction_key.pem"]
