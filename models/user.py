from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(50), primary_key=True, default=lambda: f'u_{uuid.uuid4().hex[:12]}')
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False, index=True)  # Add index for search
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    role = db.Column(db.String(20), nullable=False, index=True)  # passenger, driver, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'role': self.role,
            'createdAt': self.created_at.isoformat()
        }