# SafeRide Backend - Driver Management Routes
# Driver registration, profile management, and vehicle information

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Driver, User, db

# Create drivers blueprint
drivers_bp = Blueprint('drivers', __name__)

@drivers_bp.route('/register', methods=['POST'])
@jwt_required()
def register_driver():
    """Register driver profile with vehicle information"""
    try:
        # Get current user from JWT
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Verify user has driver role
        if not user or user.role != 'driver':
            return jsonify({'success': False, 'error': {'code': 'DRIVER_ROLE_REQUIRED', 'message': 'User must have driver role'}}), 403
        
        # Check if driver profile already exists
        existing_driver = Driver.query.filter_by(user_id=user_id).first()
        if existing_driver:
            return jsonify({'success': False, 'error': {'code': 'ALREADY_REGISTERED', 'message': 'Driver already registered'}}), 400
        
        # Extract driver registration data
        data = request.json
        license_number = data.get('licenseNumber', '').strip()
        vehicle_make = data.get('vehicleMake', '').strip()
        vehicle_model = data.get('vehicleModel', '').strip()
        vehicle_year = data.get('vehicleYear')
        vehicle_plate = data.get('vehiclePlate', '').strip()
        
        # Validate all required fields
        if not all([license_number, vehicle_make, vehicle_model, vehicle_year, vehicle_plate]):
            return jsonify({'success': False, 'error': {'code': 'MISSING_FIELDS', 'message': 'All fields required'}}), 400
        
        # Create driver profile
        driver = Driver(
            user_id=user_id,
            license_number=license_number,
            vehicle_make=vehicle_make,
            vehicle_model=vehicle_model,
            vehicle_year=int(vehicle_year),
            vehicle_plate=vehicle_plate,
            status='pending'  # Requires admin approval
        )
        
        # Save driver profile to database
        db.session.add(driver)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Driver registration submitted',
            'data': {'driver': driver.to_dict()}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'REGISTRATION_FAILED', 'message': str(e)}}), 500

@drivers_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_driver_profile():
    """Get current driver's profile information"""
    try:
        # Get current user from JWT
        user_id = get_jwt_identity()
        driver = Driver.query.filter_by(user_id=user_id).first()
        
        # Verify driver profile exists
        if not driver:
            return jsonify({'success': False, 'error': {'code': 'DRIVER_NOT_FOUND', 'message': 'Driver profile not found'}}), 404
        
        # Return driver profile data
        return jsonify({'success': True, 'data': {'driver': driver.to_dict()}}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'FETCH_FAILED', 'message': str(e)}}), 500