from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# --- MOBILE-FRIENDLY CORS ---
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Vercel provides 'POSTGRES_URL'. 
# Note: On the Vercel dashboard, you MUST connect the Storage to your project.
DATABASE_URL = os.getenv('POSTGRES_URL')

if DATABASE_URL:
    # SQL Alchemy requires 'postgresql://' instead of 'postgres://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print("LOG: Connected to Cloud Postgres")
else:
    # If this prints in your Vercel logs, your storage isn't connected!
    print("LOG: Cloud DB not found, using local temporary storage")
    DATABASE_URL = 'sqlite:///local.db'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20))
    category = db.Column(db.String(50))
    description = db.Column(db.String(200))
    payment_method = db.Column(db.String(50))
    amount = db.Column(db.Float)

class Bank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bank_name = db.Column(db.String(100))
    balance = db.Column(db.Float)

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_name = db.Column(db.String(100))
    bill_date = db.Column(db.String(20))
    bill_amount = db.Column(db.Float)
    paid_amount = db.Column(db.Float)
    paid_date = db.Column(db.String(20))
    from_bank = db.Column(db.String(100))

# Initialize Tables
with app.app_context():
    db.create_all()

# --- EXPENSE & ANALYTICS ROUTES ---
@app.route('/api/expenses', methods=['GET', 'POST'])
def handle_expenses():
    if request.method == 'POST':
        data = request.json
        new_exp = Expense(
            date=data.get('date'),
            category=data.get('category'),
            description=data.get('description', ''),
            payment_method=data.get('payment_method', ''),
            amount=float(data.get('amount', 0))
        )
        db.session.add(new_exp)
        db.session.commit()
        return jsonify({"status": "success"}), 201
    
    expenses = Expense.query.all()
    return jsonify([{
        'id': e.id, 'date': e.date, 'category': e.category, 
        'description': e.description, 'payment_method': e.payment_method, 
        'amount': e.amount
    } for e in expenses])

@app.route('/api/expenses/<int:id>', methods=['PUT', 'DELETE'])
def update_expense(id):
    exp = Expense.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(exp)
    else:
        data = request.json
        exp.date = data.get('date')
        exp.category = data.get('category')
        exp.description = data.get('description')
        exp.amount = float(data.get('amount'))
        exp.payment_method = data.get('payment_method')
    db.session.commit()
    return jsonify({"status": "updated"})

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    expenses = Expense.query.all()
    total = sum(e.amount for e in expenses)
    cats = {}
    for e in expenses:
        cats[e.category] = cats.get(e.category, 0) + e.amount
    return jsonify({"total": total, "categories": cats})

# --- BANK ROUTES ---
@app.route('/api/banks', methods=['GET', 'POST'])
def handle_banks():
    if request.method == 'POST':
        data = request.json
        new_bank = Bank(bank_name=data.get('bank_name'), balance=float(data.get('balance', 0)))
        db.session.add(new_bank)
        db.session.commit()
        return jsonify({"status": "success"}), 201
    
    banks_list = Bank.query.all()
    return jsonify([{'id': b.id, 'bank_name': b.bank_name, 'balance': b.balance} for b in banks_list])

@app.route('/api/banks/<int:id>', methods=['PUT', 'DELETE'])
def update_bank(id):
    bank = Bank.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(bank)
    else:
        data = request.json
        bank.bank_name = data.get('bank_name')
        bank.balance = float(data.get('balance'))
    db.session.commit()
    return jsonify({"status": "updated"})

# --- BILL ROUTES ---
@app.route('/api/bills', methods=['GET', 'POST'])
def handle_bills():
    if request.method == 'POST':
        data = request.json
        new_bill = Bill(
            card_name=data.get('card_name'),
            bill_date=data.get('bill_date'),
            bill_amount=float(data.get('bill_amount', 0)),
            paid_amount=float(data.get('paid_amount', 0)),
            paid_date=data.get('paid_date'),
            from_bank=data.get('from_bank')
        )
        db.session.add(new_bill)
        db.session.commit()
        return jsonify({"status": "success"}), 201
    
    bills_list = Bill.query.all()
    return jsonify([{
        'id': b.id, 'card_name': b.card_name, 'bill_date': b.bill_date, 
        'bill_amount': b.bill_amount, 'paid_amount': b.paid_amount, 
        'paid_date': b.paid_date, 'from_bank': b.from_bank
    } for b in bills_list])

@app.route('/api/bills/<int:id>', methods=['PUT', 'DELETE'])
def update_bill(id):
    bill = Bill.query.get_or_404(id)
    if request.method == 'DELETE':
        db.session.delete(bill)
    else:
        data = request.json
        bill.card_name = data.get('card_name')
        bill.bill_date = data.get('bill_date')
        bill.bill_amount = float(data.get('bill_amount'))
        bill.paid_amount = float(data.get('paid_amount'))
        bill.paid_date = data.get('paid_date')
        bill.from_bank = data.get('from_bank')
    db.session.commit()
    return jsonify({"status": "updated"})

if __name__ == '__main__':
    app.run(debug=True, port=5001)