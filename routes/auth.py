# SafeRide Backend - Authentication Routes
# JWT-based authentication system for users

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user (passenger, driver, or admin)"""
    try:
        # Extract user data from request
        data = request.json
        email = data.get('email', '').strip().lower()  # Normalize email
        password = data.get('password', '')
        full_name = data.get('fullName', '').strip()
        phone = data.get('phone', '').strip()
        role = data.get('role', 'passenger')  # Default to passenger
        
        # Validate required fields
        if not all([email, password, full_name, phone]):
            return jsonify({'success': False, 'error': {'code': 'MISSING_FIELDS', 'message': 'All fields required'}}), 400
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': {'code': 'EMAIL_EXISTS', 'message': 'Email already registered'}}), 409
        
        # Create new user with hashed password
        user = User(
            email=email,
            password_hash=generate_password_hash(password),  # Hash password for security
            full_name=full_name,
            phone=phone,
            role=role
        )
        
        # Save user to database
        db.session.add(user)
        db.session.commit()
        
        # Generate JWT access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'data': {'user': user.to_dict(), 'accessToken': access_token}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'REGISTRATION_FAILED', 'message': str(e)}}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    try:
        # Extract login credentials
        data = request.json
        email = data.get('email', '').strip().lower()  # Normalize email
        password = data.get('password', '')
        
        # Validate credentials provided
        if not email or not password:
            return jsonify({'success': False, 'error': {'code': 'MISSING_CREDENTIALS', 'message': 'Email and password required'}}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        # Verify user exists and password matches
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'success': False, 'error': {'code': 'INVALID_CREDENTIALS', 'message': 'Invalid credentials'}}), 401
        
        # Generate JWT token for authenticated user
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': {'user': user.to_dict(), 'accessToken': access_token}
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'LOGIN_FAILED', 'message': str(e)}}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user's profile information (JWT protected)"""
    try:
        # Extract user ID from JWT token
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Verify user exists in database
        if not user:
            return jsonify({'success': False, 'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}}), 404
        
        return jsonify({'success': True, 'data': {'user': user.to_dict()}}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'PROFILE_FETCH_FAILED', 'message': str(e)}}), 500