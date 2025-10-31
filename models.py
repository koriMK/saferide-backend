from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='passenger')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'fullName': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

class Driver(db.Model):
    __tablename__ = 'drivers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    license_number = db.Column(db.String(50), nullable=False)
    vehicle_make = db.Column(db.String(50), nullable=False)
    vehicle_model = db.Column(db.String(50), nullable=False)
    vehicle_year = db.Column(db.Integer, nullable=False)
    vehicle_plate = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    is_online = db.Column(db.Boolean, default=False)
    total_earnings = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='driver_profile')
    
    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'licenseNumber': self.license_number,
            'vehicleMake': self.vehicle_make,
            'vehicleModel': self.vehicle_model,
            'vehicleYear': self.vehicle_year,
            'vehiclePlate': self.vehicle_plate,
            'status': self.status,
            'isOnline': self.is_online,
            'totalEarnings': self.total_earnings
        }

class Trip(db.Model):
    __tablename__ = 'trips'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    passenger_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    driver_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    pickup_latitude = db.Column(db.Float, nullable=False)
    pickup_longitude = db.Column(db.Float, nullable=False)
    pickup_address = db.Column(db.String(255), nullable=False)
    destination_latitude = db.Column(db.Float, nullable=False)
    destination_longitude = db.Column(db.Float, nullable=False)
    destination_address = db.Column(db.String(255), nullable=False)
    fare = db.Column(db.Float, nullable=False)
    distance = db.Column(db.Float)
    status = db.Column(db.String(20), default='requested')
    payment_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    passenger = db.relationship('User', foreign_keys=[passenger_id], backref='passenger_trips')
    driver = db.relationship('User', foreign_keys=[driver_id], backref='driver_trips')
    
    def to_dict(self):
        return {
            'id': self.id,
            'passengerId': self.passenger_id,
            'driverId': self.driver_id,
            'pickupLatitude': self.pickup_latitude,
            'pickupLongitude': self.pickup_longitude,
            'pickupAddress': self.pickup_address,
            'destinationLatitude': self.destination_latitude,
            'destinationLongitude': self.destination_longitude,
            'destinationAddress': self.destination_address,
            'fare': self.fare,
            'distance': self.distance,
            'status': self.status,
            'paymentStatus': self.payment_status,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = db.Column(db.String(36), db.ForeignKey('trips.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    checkout_request_id = db.Column(db.String(100))
    mpesa_receipt_number = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    trip = db.relationship('Trip', backref='payments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'tripId': self.trip_id,
            'amount': self.amount,
            'phone': self.phone,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

class Config(db.Model):
    __tablename__ = 'config'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value
        }