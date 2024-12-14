from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

# Initialize the Flask application
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tax_tracking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class TaxRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(10), nullable=False, default='unpaid')
    due_date = db.Column(db.Date, nullable=False)

# Routes
@app.route('/')
def index():
    records = TaxRecord.query.all()
    current_year = datetime.now().year
    due_dates = [f"{current_year}-04-15", f"{current_year}-06-15", f"{current_year}-09-15", f"{current_year + 1}-01-15"]
    return render_template('index.html', records=records, due_dates=due_dates)

@app.route('/add', methods=['POST'])
def add_record():
    company = request.form['company']
    amount = float(request.form['amount'])
    payment_date = request.form['payment_date']
    payment_date = datetime.strptime(payment_date, '%Y-%m-%d') if payment_date else None
    status = request.form['status']
    due_date = request.form['due_date']
    due_date = datetime.strptime(due_date, '%Y-%m-%d')

    new_record = TaxRecord(company=company, amount=amount, payment_date=payment_date, status=status, due_date=due_date)
    db.session.add(new_record)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_record(id):
    record = TaxRecord.query.get_or_404(id)
    if request.method == 'POST':
        record.company = request.form['company']
        record.amount = float(request.form['amount'])
        payment_date = request.form['payment_date']
        record.payment_date = datetime.strptime(payment_date, '%Y-%m-%d') if payment_date else None
        record.status = request.form['status']
        due_date = request.form['due_date']
        record.due_date = datetime.strptime(due_date, '%Y-%m-%d')

        db.session.commit()
        return redirect(url_for('index'))

    # Generate due dates dynamically
    current_year = datetime.now().year
    due_dates = [f"{current_year}-04-15", f"{current_year}-06-15", f"{current_year}-09-15", f"{current_year + 1}-01-15"]

    return render_template('update.html', record=record, due_dates=due_dates)


@app.route('/delete/<int:id>', methods=['POST'])
def delete_record(id):
    record = TaxRecord.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/filter', methods=['GET'])
def filter_by_due_date():
    due_date = request.args.get('due_date')
    due_date = datetime.strptime(due_date, '%Y-%m-%d')
    records = TaxRecord.query.filter_by(due_date=due_date).all()
    total_amount = sum(record.amount for record in records)
    tax_rate = float(request.args.get('tax_rate', 0))
    tax_due = total_amount * tax_rate
    return jsonify({
        'records': [
            {
                'id': record.id,
                'company': record.company,
                'amount': record.amount,
                'payment_date': record.payment_date.strftime('%Y-%m-%d') if record.payment_date else 'NA',
                'status': record.status,
                'due_date': record.due_date.strftime('%Y-%m-%d')
            } for record in records
        ],
        'total_amount': total_amount,
        'tax_due': tax_due
    })

if __name__ == '__main__':
    app.run(debug=True)