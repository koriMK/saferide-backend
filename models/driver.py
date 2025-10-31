from . import db
from datetime import datetime
import uuid

class Driver(db.Model):
    __tablename__ = 'drivers'
    
    id = db.Column(db.String(50), primary_key=True, default=lambda: f'd_{uuid.uuid4().hex[:12]}')
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), unique=True, nullable=False)
    
    # Vehicle
    vehicle_make = db.Column(db.String(100))
    vehicle_model = db.Column(db.String(100))
    vehicle_year = db.Column(db.Integer)
    vehicle_plate = db.Column(db.String(50))
    vehicle_color = db.Column(db.String(50))
    
    # Documents
    document_id_card = db.Column(db.String(500))
    document_license = db.Column(db.String(500))
    document_insurance = db.Column(db.String(500))
    document_logbook = db.Column(db.String(500))
    
    # Stats
    rating = db.Column(db.Numeric(3, 2), default=0.00)
    total_trips = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Status
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)  # pending, approved, suspended
    is_online = db.Column(db.Boolean, default=False, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='driver_profile')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'userId': self.user_id,
            'name': self.user.name if self.user else None,
            'email': self.user.email if self.user else None,
            'phone': self.user.phone if self.user else None,
            'vehicle': {
                'make': self.vehicle_make,
                'model': self.vehicle_model,
                'year': self.vehicle_year,
                'plate': self.vehicle_plate,
                'color': self.vehicle_color
            },
            'documents': {
                'idCard': bool(self.document_id_card),
                'license': bool(self.document_license),
                'insurance': bool(self.document_insurance),
                'logbook': bool(self.document_logbook)
            },
            'rating': float(self.rating) if self.rating else 0,
            'totalTrips': self.total_trips,
            'totalEarnings': float(self.total_earnings) if self.total_earnings else 0,
            'status': self.status,
            'isOnline': self.is_online,
            'createdAt': self.created_at.isoformat()
        }