# SafeRide Backend - Driver Management Routes
# Driver registration, profile management, and vehicle information

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Driver, User, Trip
from models import db
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
import uuid

# Create drivers blueprint
drivers_bp = Blueprint('drivers', __name__)

UPLOAD_FOLDER = 'uploads/documents'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@drivers_bp.route('/available-trips', methods=['GET'])
@jwt_required()
def get_available_trips():
    """Get available trips for driver"""
    try:
        # Get current user from JWT
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'driver':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Only drivers can view available trips'
                }
            }), 403
        
        # Get trips with status 'requested' with optimization
        trips = Trip.query.options(
            db.joinedload(Trip.passenger)
        ).filter_by(status='requested').order_by(Trip.created_at.desc()).limit(20).all()
        
        return jsonify({
            'success': True,
            'data': {
                'trips': [trip.to_dict() for trip in trips]
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FETCH_FAILED',
                'message': str(e)
            }
        }), 500

@drivers_bp.route('/status', methods=['PUT'])
@jwt_required()
def update_driver_status():
    """Update driver online status"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'driver':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Only drivers can update status'
                }
            }), 403
        
        # Extract driver registration data
        data = request.json
        is_online = data.get('isOnline')
        
        if is_online is None:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_FIELD',
                    'message': 'isOnline field is required'
                }
            }), 400
        
        driver = Driver.query.filter_by(user_id=user_id).first()
        
        if not driver:
            # Create driver profile if it doesn't exist
            driver = Driver(user_id=user_id, status='approved')  # Auto-approve for demo
            db.session.add(driver)
        
        driver.is_online = is_online
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Status updated',
            'data': {
                'isOnline': driver.is_online
            }
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

@drivers_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_driver_profile():
    """Get driver profile"""
    try:
        # Get current user from JWT
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'driver':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Only drivers can access this endpoint'
                }
            }), 403
        
        driver = Driver.query.filter_by(user_id=user_id).first()
        
        # Verify driver profile exists
        if not driver:
            # Create driver profile if it doesn't exist
            driver = Driver(user_id=user_id)
            db.session.add(driver)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'data': driver.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FETCH_FAILED',
                'message': str(e)
            }
        }), 500

@drivers_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_driver_profile():
    """Update driver profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'driver':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Only drivers can update profile'
                }
            }), 403
        
        data = request.json
        vehicle = data.get('vehicle', {})
        
        # Get or create driver profile
        driver = Driver.query.filter_by(user_id=user_id).first()
        if not driver:
            driver = Driver(user_id=user_id)
            db.session.add(driver)
        
        # Update vehicle information with validation
        if vehicle:
            # Sanitize and validate inputs
            make = str(vehicle.get('make', driver.vehicle_make or ''))[:100]
            model = str(vehicle.get('model', driver.vehicle_model or ''))[:100]
            plate = str(vehicle.get('plate', driver.vehicle_plate or ''))[:20]
            color = str(vehicle.get('color', driver.vehicle_color or ''))[:50]
            
            driver.vehicle_make = make.strip() if make else driver.vehicle_make
            driver.vehicle_model = model.strip() if model else driver.vehicle_model
            driver.vehicle_year = vehicle.get('year', driver.vehicle_year)
            driver.vehicle_plate = plate.strip().upper() if plate else driver.vehicle_plate
            driver.vehicle_color = color.strip() if color else driver.vehicle_color
        
        driver.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'data': driver.to_dict()
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

@drivers_bp.route('/upload-document', methods=['POST'])
@jwt_required()
def upload_document():
    """Upload driver document"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'driver':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Only drivers can upload documents'
                }
            }), 403
        
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NO_FILE',
                    'message': 'No file provided'
                }
            }), 400
        
        file = request.files['file']
        document_type = request.form.get('type')  # idCard, license, insurance, logbook
        
        if not document_type or document_type not in ['idCard', 'license', 'insurance', 'logbook']:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_TYPE',
                    'message': 'Invalid document type'
                }
            }), 400
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NO_FILE',
                    'message': 'No file selected'
                }
            }), 400
        
        if file and allowed_file(file.filename):
            # Create upload directory if it doesn't exist
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # Generate secure unique filename
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{user_id}_{document_type}_{uuid.uuid4().hex[:8]}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # Validate file path is within upload directory
            if not os.path.abspath(filepath).startswith(os.path.abspath(UPLOAD_FOLDER)):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_PATH',
                        'message': 'Invalid file path'
                    }
                }), 400
            
            # Save file
            file.save(filepath)
            
            # Update driver profile
            driver = Driver.query.filter_by(user_id=user_id).first()
            if not driver:
                driver = Driver(user_id=user_id)
                db.session.add(driver)
            
            if document_type == 'idCard':
                driver.document_id_card = filepath
            elif document_type == 'license':
                driver.document_license = filepath
            elif document_type == 'insurance':
                driver.document_insurance = filepath
            elif document_type == 'logbook':
                driver.document_logbook = filepath
            
            # Check if all required documents are uploaded
            if (driver.document_id_card and driver.document_license and 
                driver.vehicle_make and driver.vehicle_plate):
                driver.status = 'pending'  # Ready for admin review
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Document uploaded successfully',
                'data': {
                    'type': document_type,
                    'uploaded': True
                }
            }), 200
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'INVALID_FILE',
                'message': 'Invalid file type. Allowed: pdf, png, jpg, jpeg'
            }
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'UPLOAD_FAILED',
                'message': str(e)
            }
        }), 500

@drivers_bp.route('/earnings', methods=['GET'])
@jwt_required()
def get_driver_earnings():
    """Get driver earnings summary"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'driver':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Only drivers can view earnings'
                }
            }), 403
        
        # Get completed trips
        completed_trips = Trip.query.filter_by(
            driver_id=user_id,
            status='completed'
        ).all()
        
        # Calculate earnings
        total_earnings = sum(float(trip.fare) for trip in completed_trips)
        total_trips = len(completed_trips)
        
        # Get today's earnings
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_trips = [t for t in completed_trips if t.completed_at and t.completed_at >= today_start]
        today_earnings = sum(float(trip.fare) for trip in today_trips)
        
        # Get this week's earnings
        week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_trips = [t for t in completed_trips if t.completed_at and t.completed_at >= week_start]
        week_earnings = sum(float(trip.fare) for trip in week_trips)
        
        # Get driver rating
        driver = Driver.query.filter_by(user_id=user_id).first()
        rating = float(driver.rating) if driver and driver.rating else 0
        
        return jsonify({
            'success': True,
            'data': {
                'totalEarnings': total_earnings,
                'totalTrips': total_trips,
                'todayEarnings': today_earnings,
                'todayTrips': len(today_trips),
                'weekEarnings': week_earnings,
                'weekTrips': len(week_trips),
                'averagePerTrip': total_earnings / total_trips if total_trips > 0 else 0,
                'rating': rating
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FETCH_FAILED',
                'message': str(e)
            }
        }), 500

@drivers_bp.route('/payout', methods=['POST'])
@jwt_required()
def request_payout():
    """Request driver payout"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'driver':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Only drivers can request payouts'
                }
            }), 403
        
        data = request.json
        amount = data.get('amount')
        phone = data.get('phone')
        
        if not amount or not phone:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'Amount and phone number are required'
                }
            }), 400
        
        # Mock payout processing
        payout_id = f'po_{uuid.uuid4().hex[:12]}'
        
        return jsonify({
            'success': True,
            'message': 'Payout request submitted successfully',
            'data': {
                'payoutId': payout_id,
                'amount': amount,
                'phone': phone,
                'status': 'processing'
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'PAYOUT_FAILED',
                'message': str(e)
            }
        }), 500
