from datetime import datetime
from db import db

class Guest(db.Model):
    """Guest Model for storing guest related details"""
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    citizen_number = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    emergency_contact = db.Column(db.String(50), nullable=False)
    address = db.Column(db.Text, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    food_preference = db.Column(db.String(10), nullable=False)  # 'veg' or 'non-veg'
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=True)
    last_bill_date = db.Column(db.Date, nullable=True)
    
    # Foreign Keys
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    
    # Relationships
    room = db.relationship('Room', backref='guests', lazy=True)
    bills = db.relationship('Bill', backref='guest', lazy=True)
    payments = db.relationship('Payment', backref='guest', lazy=True)
    
    def __repr__(self):
        return f'<Guest {self.full_name}>'

class Room(db.Model):
    """Room Model for storing room related details"""
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    room_type = db.Column(db.String(20), nullable=False)  # '1 seater', '3 seater', '4 seater'
    price_per_month = db.Column(db.Float, nullable=False)
    occupancy = db.Column(db.Boolean, default=False)
    
    # Relationships
    bills = db.relationship('Bill', backref='room', lazy=True)
    
    def __init__(self, room_number, room_type, occupancy=False):
        self.room_number = room_number
        self.room_type = room_type
        self.occupancy = occupancy
        # Set price based on room type
        if room_type == '1 seater':
            self.price_per_month = 12000
        elif room_type == '3 seater':
            self.price_per_month = 10000
        elif room_type == '4 seater':
            self.price_per_month = 9000
        else:
            raise ValueError('Invalid room type')
    
    def __repr__(self):
        return f'<Room {self.room_number}>'

class Bill(db.Model):
    """Bill Model for storing billing information"""
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    billing_month = db.Column(db.Integer, nullable=False)
    billing_year = db.Column(db.Integer, nullable=False)
    total_days = db.Column(db.Integer, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    generated_date = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_path = db.Column(db.String(255), nullable=True)
    
    # Relationships
    payments = db.relationship('Payment', backref='bill', lazy=True)
    
    def __repr__(self):
        return f'<Bill {self.id} for Guest {self.guest_id}>'

class Payment(db.Model):
    """Payment Model for storing payment history"""
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), nullable=False)  # 'informed & pending', 'paid', 'advance'
    
    def __repr__(self):
        return f'<Payment {self.id} - {self.amount}>'

class Expense(db.Model):
    """Expense Model for storing expense related details"""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # food, vegetables, snacks, milk, electricity, salary, water, meat, essentials
    description = db.Column(db.Text, nullable=True)  # Additional remarks
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Expense {self.category} - {self.amount}>'