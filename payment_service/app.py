from flask import Flask,request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import datetime
import time


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db_payment:5432/trans_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'super-secret-key'

db = SQLAlchemy(app)
# bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Transaction Model
class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    payer_us = db.Column(db.String(50), nullable=False)
    receiver_us = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, nullable=False)


class Balance(db.Model):
    __tablename__ = 'balance'
    username = db.Column(db.String(50), primary_key=True)
    balance = db.Column(db.Float, nullable=False)


from datetime import datetime

@app.route('/pay', methods=['POST'])
def pay():
    payer_us = request.form.get('payer_us')
    receiver_us = request.form.get('receiver_us')
    amount = request.form.get('amount')
    
    # Conversion from string to float
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({'Error': 'Invalid amount'}), 400

    payer_balance = Balance.query.filter_by(username=payer_us).first()
    receiver_balance = Balance.query.filter_by(username=receiver_us).first()

    if not payer_balance:
        return jsonify({'Error': f'Payer user {payer_us} not found'}), 404
    if not receiver_balance:
        return jsonify({'Error': f'Receiver user {receiver_us} not found'}), 404

    # Controlla che il saldo del pagatore sia sufficiente
    if payer_balance.balance >= amount:
        # Inserisci una nuova transazione nel database
        new_transaction = Transaction(
            payer_us=payer_us,
            receiver_us=receiver_us,
            amount=amount,
            currency='Memecoins',
            date=datetime.now()
        )
        db.session.add(new_transaction)

        # Scala i soldi dal saldo del pagatore e aggiungili a quello del ricevente
        payer_balance.balance -= amount
        receiver_balance.balance += amount

        try:
            db.session.commit()
            return jsonify({'msg': 'Payment successfully executed'}), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'Error': 'Transaction failed', 'details': str(e)}), 500
    else:
        return jsonify({'Error': 'Balance not sufficient to carry out the operation'}), 400

#  # Commit with 3 re-try before failure
#         for attempt in range(3):
#             try:
#                 db.session.commit()
#                 return jsonify({'msg': 'Payment successfully executed'}), 200
#             except SQLAlchemyError as e:
#                 db.session.rollback()
#                 if attempt < 3 - 1:  # Se non è l'ultimo tentativo
#                     time.sleep(1)   # Aspetta prima di riprovare
#                 else:  # Dopo l'ultimo tentativo, ritorna un errore
#                     return jsonify({'Error': 'Transaction failed after retries', 'details': str(e)}), 500
#         return jsonify({'msg': 'Payment successfully executed'}), 200


@app.route('/buycurrency', methods = ['POST'])
def buycurrency():  
    username = request.form.get('username')
    amount = request.form.get('amount')
    method = request.form.get('payment_method')

    # Conversion from string to float
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({'Error': 'Invalid amount'}), 400
    
    #inserisci una transazione nel db 
    paying_t = Transaction(
            payer_us=username,
            receiver_us='system',
            amount=amount,
            currency='Euro',
            date=datetime.now()
        )
    db.session.add(paying_t)
    receiving_t = Transaction(
            payer_us='system',
            receiver_us=username,
            amount=amount,
            currency='Memecoin',
            date=datetime.now()
        )
    db.session.add(receiving_t)

    current_balance = Balance.query.filter_by(username=username).first()
    if not current_balance:
        return jsonify({'Error': f'Payer user {username} not found'}), 404
    current_balance.balance +=amount
    try:
        db.session.commit()
        return jsonify({'username': username,'balance':current_balance.balance,'msg': 'In-game currency purchased successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'Error': 'Internal server error or payment processing issue', 'details': str(e)}), 500

@app.route('/viewTrans', methods = ['GET'])
def viewTrans():  
    username = request.args.get('username')
    # Search in the transaction db
    payed_t = Transaction.query.filter_by(payer_us=username).all()
    received_t = Transaction.query.filter_by(receiver_us=username).all()
    transaction_list = []
    if payed_t:
        result = [{'id': t.id, 'payer_us': username, 'receiver_us': t.receiver_us,'amount' : f'-{t.amount}', 'currency':t.currency, 'date':t.date} for t in payed_t]   
        transaction_list += result
    if received_t:
        result = [{'id': t.id, 'payer_us': t.payer_us, 'receiver_us': username,'amount' : f'+{t.amount}', 'currency':t.currency, 'date':t.date} for t in received_t]   
        transaction_list += result
    return jsonify(transaction_list), 200

@app.route('/newBalance', methods=['POST'])
def newBalance():
    data = request.get_json()
    username = data.get('username')
    res = Balance.query.filter_by(username=username).all()
    if not res:
        new_balance = Balance(username=username, balance=0)
        db.session.add(new_balance)
        try:
            db.session.commit()
            return jsonify({'msg': f'Corretcly created a balance for {username}'}), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'Error': 'Committing error', 'details': str(e)}), 500
    else:
        return jsonify({'Error': 'Username already inserted in balance db'}), 400

@app.route('/getBalance', methods=['GET'])
def getBalance():
    username = request.args.get('username')
    res = Balance.query.filter_by(username=username).first()
    if res: 
        return jsonify({'username': res.username, 'balance': res.balance}), 200
    else:
        return jsonify({'Error': 'Not found balance for that user'}), 404
    
@app.route('/deleteBalance', methods=['DELETE'])
def deleteBalance():
    data = request.get_json()
    username = data.get('username')
    res = Balance.query.filter_by(username=username).first()
    if res:
        db.session.delete(res)
        try:
            db.session.commit()
            return jsonify({'msg': f'Corretcly deleted balance for {username}'}), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'Error': 'Committing error', 'details': str(e)}), 500
    else:
        return jsonify({'Error': 'Balance not found'}), 400