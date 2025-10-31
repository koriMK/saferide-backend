# SafeRide Backend - Database Models
# SQLAlchemy models for ride-sharing application

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

# Initialize SQLAlchemy instance
db = SQLAlchemy()

class User(db.Model):
    """User model for passengers, drivers, and admins"""
    __tablename__ = 'users'
    
    # Primary key with UUID for security
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # User authentication fields
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # Hashed password
    # User profile information
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='passenger')  # passenger, driver, admin
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert user object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'email': self.email,
            'fullName': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

class Driver(db.Model):
    """Driver profile model with vehicle and verification information"""
    __tablename__ = 'drivers'
    
    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Foreign key to User table
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    # Driver license information
    license_number = db.Column(db.String(50), nullable=False)
    # Vehicle information
    vehicle_make = db.Column(db.String(50), nullable=False)
    vehicle_model = db.Column(db.String(50), nullable=False)
    vehicle_year = db.Column(db.Integer, nullable=False)
    vehicle_plate = db.Column(db.String(20), nullable=False)
    # Driver status and activity
    status = db.Column(db.String(20), default='pending')  # pending, approved, suspended
    is_online = db.Column(db.Boolean, default=False)      # Online/offline status
    total_earnings = db.Column(db.Float, default=0.0)     # Total earnings from trips
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to User model
    user = db.relationship('User', backref='driver_profile')
    
    def to_dict(self):
        """Convert driver object to dictionary for JSON serialization"""
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
    """Trip model for ride requests and bookings"""
    __tablename__ = 'trips'
    
    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # User relationships
    passenger_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    driver_id = db.Column(db.String(36), db.ForeignKey('users.id'))  # Assigned when accepted
    # Pickup location
    pickup_latitude = db.Column(db.Float, nullable=False)
    pickup_longitude = db.Column(db.Float, nullable=False)
    pickup_address = db.Column(db.String(255), nullable=False)
    # Destination location
    destination_latitude = db.Column(db.Float, nullable=False)
    destination_longitude = db.Column(db.Float, nullable=False)
    destination_address = db.Column(db.String(255), nullable=False)
    # Trip details
    fare = db.Column(db.Float, nullable=False)           # Calculated fare
    distance = db.Column(db.Float)                       # Distance in kilometers
    status = db.Column(db.String(20), default='requested')  # requested, accepted, driving, completed
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships to User model
    passenger = db.relationship('User', foreign_keys=[passenger_id], backref='passenger_trips')
    driver = db.relationship('User', foreign_keys=[driver_id], backref='driver_trips')
    
    def to_dict(self):
        """Convert trip object to dictionary for JSON serialization"""
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
    """Payment model for M-Pesa transactions"""
    __tablename__ = 'payments'
    
    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Foreign key to Trip
    trip_id = db.Column(db.String(36), db.ForeignKey('trips.id'), nullable=False)
    # Payment details
    amount = db.Column(db.Float, nullable=False)         # Payment amount
    phone = db.Column(db.String(20), nullable=False)     # M-Pesa phone number
    # M-Pesa transaction details
    checkout_request_id = db.Column(db.String(100))      # M-Pesa STK push ID
    mpesa_receipt_number = db.Column(db.String(50))      # M-Pesa receipt number
    status = db.Column(db.String(20), default='pending') # pending, paid, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to Trip model
    trip = db.relationship('Trip', backref='payments')
    
    def to_dict(self):
        """Convert payment object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'tripId': self.trip_id,
            'amount': self.amount,
            'phone': self.phone,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

class Config(db.Model):
    """Configuration model for dynamic app settings"""
    __tablename__ = 'config'
    
    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Configuration key-value pairs
    key = db.Column(db.String(100), unique=True, nullable=False)  # Configuration key
    value = db.Column(db.Text, nullable=False)                    # Configuration value
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert config object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value
        }