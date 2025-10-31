from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = data.get('fullName', '').strip()
        phone = data.get('phone', '').strip()
        role = data.get('role', 'passenger')
        
        if not all([email, password, full_name, phone]):
            return jsonify({'success': False, 'error': {'code': 'MISSING_FIELDS', 'message': 'All fields required'}}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': {'code': 'EMAIL_EXISTS', 'message': 'Email already registered'}}), 409
        
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            phone=phone,
            role=role
        )
        
        db.session.add(user)
        db.session.commit()
        
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
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': {'code': 'MISSING_CREDENTIALS', 'message': 'Email and password required'}}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'success': False, 'error': {'code': 'INVALID_CREDENTIALS', 'message': 'Invalid credentials'}}), 401
        
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
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}}), 404
        
        return jsonify({'success': True, 'data': {'user': user.to_dict()}}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'PROFILE_FETCH_FAILED', 'message': str(e)}}), 500