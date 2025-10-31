from . import db
from datetime import datetime
import uuid

class Rating(db.Model):
    __tablename__ = 'ratings'
    
    id = db.Column(db.String(50), primary_key=True, default=lambda: f'rating_{uuid.uuid4().hex[:12]}')
    trip_id = db.Column(db.String(50), db.ForeignKey('trips.id'), nullable=False, unique=True)
    
    # Rating details
    passenger_rating = db.Column(db.Integer)  # Passenger rates driver (1-5)
    driver_rating = db.Column(db.Integer)     # Driver rates passenger (1-5)
    
    passenger_feedback = db.Column(db.Text)
    driver_feedback = db.Column(db.Text)
    
    # Categories
    cleanliness_rating = db.Column(db.Integer)
    punctuality_rating = db.Column(db.Integer)
    communication_rating = db.Column(db.Integer)
    safety_rating = db.Column(db.Integer)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'tripId': self.trip_id,
            'passengerRating': self.passenger_rating,
            'driverRating': self.driver_rating,
            'passengerFeedback': self.passenger_feedback,
            'driverFeedback': self.driver_feedback,
            'cleanlinessRating': self.cleanliness_rating,
            'punctualityRating': self.punctuality_rating,
            'communicationRating': self.communication_rating,
            'safetyRating': self.safety_rating,
            'createdAt': self.created_at.isoformat()
        }