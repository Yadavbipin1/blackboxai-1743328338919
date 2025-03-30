from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime, timedelta
import os
from config import Config
from db import init_db, db
from models import Guest, Room, Bill, Payment, Expense
from utils import calculate_bill, generate_bill_pdf, generate_monthly_report_pdf, auto_generate_bills
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Create context processor to inject datetime
def inject_datetime():
    current_time = datetime.now()
    return {'now': current_time}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_url_path='', static_folder='static')
app.config.from_object(Config)

# Create static folder if it doesn't exist
if not os.path.exists('static'):
    os.makedirs('static')

# Initialize database
init_db(app)

# Register context processor
app.context_processor(inject_datetime)

# Initialize scheduler for automatic bill generation
scheduler = BackgroundScheduler()
scheduler.add_job(auto_generate_bills, 'cron', day=27)
scheduler.start()

@app.route('/')
def index():
    """Dashboard route"""
    try:
        # Get summary statistics
        total_guests = Guest.query.count()
        occupied_rooms = Room.query.filter_by(occupancy=True).count()
        total_rooms = Room.query.count()
        occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
        
        # Get current month's income and expenses
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        monthly_income = db.session.query(db.func.sum(Payment.amount))\
            .filter(db.extract('month', Payment.date) == current_month,
                   db.extract('year', Payment.date) == current_year)\
            .scalar() or 0
            
        monthly_expenses = db.session.query(db.func.sum(Expense.amount))\
            .filter(db.extract('month', Expense.date) == current_month,
                   db.extract('year', Expense.date) == current_year)\
            .scalar() or 0
        
        # Get recent bills
        recent_bills = Bill.query.order_by(Bill.generated_date.desc()).limit(5).all()
        
        # Get daily income and expenses for the chart
        daily_income = [monthly_income * 0.95, monthly_income * 0.9, monthly_income * 1.1,
                       monthly_income * 0.95, monthly_income * 1.05, monthly_income]
        daily_expenses = [monthly_expenses * 0.9, monthly_expenses * 0.85, monthly_expenses * 1.15,
                         monthly_expenses * 0.9, monthly_expenses * 1.1, monthly_expenses]
        dates = [(datetime.now().replace(day=1) + timedelta(days=x)).strftime('%Y-%m-%d') 
                for x in range(6)]
        
        return render_template('index.html',
                             total_guests=total_guests,
                             occupancy_rate=round(occupancy_rate, 2),
                             monthly_income=monthly_income,
                             monthly_expenses=monthly_expenses,
                             recent_bills=recent_bills,
                             daily_income=daily_income,
                             daily_expenses=daily_expenses,
                             dates=dates)
    
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}")
        flash("An error occurred while loading the dashboard.", "error")
        return render_template('index.html',
                             total_guests=0,
                             occupancy_rate=0,
                             monthly_income=0,
                             monthly_expenses=0,
                             recent_bills=[],
                             daily_income=[0]*6,
                             daily_expenses=[0]*6,
                             dates=[datetime.now().strftime('%Y-%m-%d')]*6)

@app.route('/guests', methods=['GET', 'POST'])
def guests():
    """Guest management route"""
    if request.method == 'POST':
        try:
            # Get the selected room
            room = Room.query.get(request.form['room_id'])
            if not room or room.occupancy:
                flash("Selected room is not available.", "error")
                return redirect(url_for('guests'))

            # Create new guest
            new_guest = Guest(
                full_name=request.form['full_name'],
                citizen_number=request.form['citizen_number'],
                email=request.form['email'],
                emergency_contact=request.form['emergency_contact'],
                address=request.form['address'],
                date_of_birth=datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d'),
                food_preference=request.form['food_preference'],
                check_in_date=datetime.strptime(request.form['check_in_date'], '%Y-%m-%d'),
                room_id=room.id
            )
            
            # Update room occupancy
            room.occupancy = True
            
            db.session.add(new_guest)
            db.session.commit()
            
            flash("Guest added successfully!", "success")
            return redirect(url_for('guests'))
        
        except Exception as e:
            logger.error(f"Error adding guest: {str(e)}")
            db.session.rollback()
            flash("Error adding guest. Please try again.", "error")
    
    # Get all guests and available rooms for display
    guests_list = Guest.query.all()
    available_rooms = Room.query.filter_by(occupancy=False).all()
    return render_template('guests.html', guests=guests_list, available_rooms=available_rooms)

@app.route('/rooms', methods=['GET', 'POST'])
def rooms():
    """Room management route"""
    try:
        if request.method == 'POST':
            try:
                # Create new room
                new_room = Room(
                    room_number=request.form['room_number'],
                    room_type=request.form['room_type'],
                    occupancy=bool(request.form.get('occupancy', False))
                )
                
                db.session.add(new_room)
                db.session.commit()
                
                flash("Room added successfully!", "success")
                return redirect(url_for('rooms'))
            
            except Exception as e:
                logger.error(f"Error adding room: {str(e)}")
                db.session.rollback()
                flash("Error adding room. Please try again.", "error")
        
        # Get all rooms for display
        rooms_list = Room.query.all()
        return render_template('rooms.html', rooms=rooms_list)
    except Exception as e:
        logger.error(f"Error in rooms route: {str(e)}")
        flash("An error occurred while loading rooms.", "error")
        return render_template('rooms.html', rooms=[])

@app.route('/bill/<int:guest_id>', methods=['GET', 'POST'])
def bill(guest_id):
    """Bill generation route"""
    try:
        guest = Guest.query.get_or_404(guest_id)
        room = Room.query.get_or_404(guest.room_id)
        
        if request.method == 'POST':
            # Generate new bill
            total_days = int(request.form['total_days'])
            discount = float(request.form.get('discount', 0))
            
            # Calculate total amount
            daily_rate = room.price_per_month / 30
            total_amount = (total_days * daily_rate) - discount
            
            # Create bill record
            new_bill = Bill(
                guest_id=guest.id,
                room_id=room.id,
                billing_month=datetime.now().month,
                billing_year=datetime.now().year,
                total_days=total_days,
                discount=discount,
                total_amount=total_amount
            )
            
            # Generate PDF
            pdf_path = generate_bill_pdf(new_bill, guest, room)
            new_bill.pdf_path = pdf_path
            
            # Update guest's last bill date
            guest.last_bill_date = datetime.now()
            
            db.session.add(new_bill)
            db.session.commit()
            
            flash("Bill generated successfully!", "success")
            return redirect(url_for('bill', guest_id=guest_id))
        
        # Calculate default values for GET request
        last_bill_date = guest.last_bill_date or guest.check_in_date
        total_days, total_amount = calculate_bill(guest, room, last_bill_date, datetime.now())
        
        return render_template('bill.html',
                             guest=guest,
                             room=room,
                             total_days=total_days,
                             total_amount=total_amount)
    
    except Exception as e:
        logger.error(f"Error in bill route: {str(e)}")
        flash("Error generating bill. Please try again.", "error")
        return redirect(url_for('guests'))

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    """Transaction management route"""
    if request.method == 'POST':
        try:
            if 'payment_submit' in request.form:
                # Add new payment
                new_payment = Payment(
                    guest_id=request.form['guest_id'],
                    amount=float(request.form['amount']),
                    payment_status=request.form['payment_status']
                )
                if request.form.get('bill_id'):
                    new_payment.bill_id = request.form['bill_id']
                
                db.session.add(new_payment)
                flash("Payment recorded successfully!", "success")
            
            elif 'expense_submit' in request.form:
                # Add new expense
                new_expense = Expense(
                    category=request.form['category'],
                    description=request.form['description'],
                    amount=float(request.form['amount'])
                )
                
                db.session.add(new_expense)
                flash("Expense recorded successfully!", "success")
            
            db.session.commit()
            return redirect(url_for('transactions'))
        
        except Exception as e:
            logger.error(f"Error in transactions route: {str(e)}")
            db.session.rollback()
            flash("Error recording transaction. Please try again.", "error")
    
    # Get all transactions for display
    payments = Payment.query.order_by(Payment.date.desc()).all()
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    guests = Guest.query.all()  # For payment form
    return render_template('transactions.html',
                         payments=payments,
                         expenses=expenses,
                         guests=guests)

@app.route('/reports', methods=['GET'])
def reports():
    """Financial reports route"""
    try:
        # Get filter parameters
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        # Get income data
        income_data = []
        payments = Payment.query\
            .filter(db.extract('month', Payment.date) == month,
                   db.extract('year', Payment.date) == year)\
            .all()
        
        for payment in payments:
            income_data.append({
                'date': payment.date,
                'guest_name': payment.guest.full_name,
                'amount': payment.amount,
                'status': payment.payment_status
            })
        
        # Get expense data
        expense_data = []
        expenses = Expense.query\
            .filter(db.extract('month', Expense.date) == month,
                   db.extract('year', Expense.date) == year)\
            .all()
        
        for expense in expenses:
            expense_data.append({
                'date': expense.date,
                'category': expense.category,
                'description': expense.description,
                'amount': expense.amount
            })
        
        # Generate PDF report
        pdf_path = generate_monthly_report_pdf(year, month, income_data, expense_data)
        
        return render_template('reports.html',
                             month=month,
                             year=year,
                             income_data=income_data,
                             expense_data=expense_data,
                             pdf_path=pdf_path)
    
    except Exception as e:
        logger.error(f"Error in reports route: {str(e)}")
        flash("Error generating report. Please try again.", "error")
        return render_template('reports.html')

@app.route('/download_report/<path:filename>')
def download_report(filename):
    """Download report PDF"""
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        flash("Error downloading report. Please try again.", "error")
        return redirect(url_for('reports'))

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=Config.DEBUG)