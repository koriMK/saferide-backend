from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, Driver, db
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate Kenyan phone number"""
    pattern = r'^(\+254|254|0)?[17]\d{8}$'
    return re.match(pattern, phone) is not None

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['email', 'password', 'name', 'role']
        if data.get('role') != 'admin':
            required_fields.append('phone')
            
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_FIELD',
                        'message': f'Missing required field: {field}'
                    }
                }), 400
        
        email = data['email'].lower()
        password = data['password']
        name = data['name']
        phone = data.get('phone')
        role = data['role']
        
        # Validate email
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_EMAIL',
                    'message': 'Invalid email format'
                }
            }), 400
        
        # Validate phone (skip validation for admin with default phone)
        if role != 'admin' and not validate_phone(phone):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_PHONE',
                    'message': 'Invalid phone number. Use format: +254712345678'
                }
            }), 400
        
        # Validate role
        if role not in ['passenger', 'driver', 'admin']:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_ROLE',
                    'message': 'Role must be passenger, driver, or admin'
                }
            }), 400
        
        # Validate password strength
        try:
            from models import Config
            min_password_length = int(Config.get_value('MIN_PASSWORD_LENGTH', '8'))
        except:
            min_password_length = 8
            
        if len(password) < min_password_length:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'WEAK_PASSWORD',
                    'message': f'Password must be at least {min_password_length} characters'
                }
            }), 400
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'EMAIL_EXISTS',
                    'message': 'Email already registered'
                }
            }), 409
        
        # Only check phone uniqueness for non-admin users
        if role != 'admin' and User.query.filter_by(phone=phone).first():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PHONE_EXISTS',
                    'message': 'Phone number already registered'
                }
            }), 409
        
        # Create user (admin gets null phone)
        user = User(
            email=email,
            name=name,
            phone=phone if role != 'admin' else None,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # If driver, create driver profile
        if role == 'driver':
            driver = Driver(user_id=user.id)
            db.session.add(driver)
            db.session.commit()
        
        # Generate JWT token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'token': access_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'REGISTRATION_FAILED',
                'message': str(e)
            }
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.json
        
        email = data.get('email', '').lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_CREDENTIALS',
                    'message': 'Email and password are required'
                }
            }), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid email or password'
                }
            }), 401
        
        # Generate JWT token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'LOGIN_FAILED',
                'message': str(e)
            }
        }), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # User profile retrieved successfully
        
        return jsonify({
            'success': True,
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FETCH_FAILED',
                'message': str(e)
            }
        }), 500