from . import db
from datetime import datetime
import uuid

class Trip(db.Model):
    __tablename__ = 'trips'
    
    id = db.Column(db.String(50), primary_key=True, default=lambda: f't_{uuid.uuid4().hex[:12]}')
    passenger_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    driver_id = db.Column(db.String(50), db.ForeignKey('users.id'))
    
    # Pickup location
    pickup_lat = db.Column(db.Numeric(10, 8), nullable=False)
    pickup_lng = db.Column(db.Numeric(11, 8), nullable=False)
    pickup_address = db.Column(db.String(500), nullable=False)
    
    # Dropoff location
    dropoff_lat = db.Column(db.Numeric(10, 8), nullable=False)
    dropoff_lng = db.Column(db.Numeric(11, 8), nullable=False)
    dropoff_address = db.Column(db.String(500), nullable=False)
    
    # Trip details
    status = db.Column(db.String(20), default='requested', nullable=False, index=True)  # Add index for filtering
    fare = db.Column(db.Numeric(10, 2), nullable=False)
    distance = db.Column(db.Numeric(10, 2), nullable=False)  # km
    duration = db.Column(db.Integer, nullable=False)  # minutes
    
    # Payment
    payment_status = db.Column(db.String(20), default='pending', nullable=False, index=True)  # Add index for filtering
    
    # Rating
    rating = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    passenger = db.relationship('User', foreign_keys=[passenger_id])
    driver = db.relationship('User', foreign_keys=[driver_id])
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'passengerId': self.passenger_id,
            'driverId': self.driver_id,
            'pickup': {
                'lat': float(self.pickup_lat),
                'lng': float(self.pickup_lng),
                'address': self.pickup_address
            },
            'dropoff': {
                'lat': float(self.dropoff_lat),
                'lng': float(self.dropoff_lng),
                'address': self.dropoff_address
            },
            'status': self.status,
            'fare': float(self.fare),
            'distance': float(self.distance),
            'duration': self.duration,
            'paymentStatus': self.payment_status,
            'rating': self.rating,
            'feedback': self.feedback,
            'createdAt': self.created_at.isoformat(),
            'acceptedAt': self.accepted_at.isoformat() if self.accepted_at else None,
            'startedAt': self.started_at.isoformat() if self.started_at else None,
            'completedAt': self.completed_at.isoformat() if self.completed_at else None
        }