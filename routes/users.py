# SafeRide Backend - User Management Routes
# Admin-only user management functionality

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User

# Create users blueprint
users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users in the system (admin only)"""
    try:
        # Get current user from JWT token
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)
        
        # Verify user has admin privileges
        if not current_user or current_user.role != 'admin':
            return jsonify({'success': False, 'error': {'code': 'ADMIN_REQUIRED', 'message': 'Admin access required'}}), 403
        
        # Fetch all users ordered by creation date
        users = User.query.order_by(User.created_at.desc()).all()
        
        # Return user list as JSON
        return jsonify({
            'success': True,
            'data': {'users': [user.to_dict() for user in users]}
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'FETCH_FAILED', 'message': str(e)}}), 500