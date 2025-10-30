from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, db

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get user profile"""
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

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """Update user profile"""
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
        
        data = request.json
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name']
        if 'phone' in data:
            # Check if phone is already taken by another user
            existing_user = User.query.filter(
                User.phone == data['phone'],
                User.id != user_id
            ).first()
            if existing_user:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'PHONE_EXISTS',
                        'message': 'Phone number already in use'
                    }
                }), 409
            user.phone = data['phone']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'UPDATE_FAILED',
                'message': str(e)
            }
        }), 500