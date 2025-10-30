from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Trip, User, Driver, db
from datetime import datetime
import math

trips_bp = Blueprint('trips', __name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance using Haversine formula"""
    try:
        from models import Config
        R = float(Config.get_value('EARTH_RADIUS_KM', '6371'))
    except:
        R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

@trips_bp.route('', methods=['POST'])
@jwt_required()
def create_trip():
    """Create new trip request"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'passenger':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Only passengers can request trips'
                }
            }), 403
        
        data = request.json
        pickup = data.get('pickup')
        dropoff = data.get('dropoff')
        
        if not pickup or not dropoff:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_LOCATION',
                    'message': 'Pickup and dropoff locations are required'
                }
            }), 400
        
        # Calculate distance
        distance = calculate_distance(
            float(pickup['lat']), float(pickup['lng']),
            float(dropoff['lat']), float(dropoff['lng'])
        )
        
        # Calculate fare using cached config values
        try:
            from models import Config
            # Cache config values to avoid repeated DB queries
            if not hasattr(create_trip, '_config_cache'):
                create_trip._config_cache = {
                    'BASE_FARE': float(Config.get_value('TRIP_BASE_FARE', '200')),
                    'RATE_PER_KM': float(Config.get_value('TRIP_RATE_PER_KM', '50')),
                    'AVERAGE_SPEED': float(Config.get_value('TRIP_AVERAGE_SPEED', '30'))
                }
            BASE_FARE = create_trip._config_cache['BASE_FARE']
            RATE_PER_KM = create_trip._config_cache['RATE_PER_KM']
            AVERAGE_SPEED = create_trip._config_cache['AVERAGE_SPEED']
        except:
            BASE_FARE = 200
            RATE_PER_KM = 50
            AVERAGE_SPEED = 30
        
        fare = BASE_FARE + (distance * RATE_PER_KM)
        duration = int((distance / AVERAGE_SPEED) * 60)  # minutes
        
        # Create trip
        trip = Trip(
            passenger_id=user_id,
            pickup_lat=pickup['lat'],
            pickup_lng=pickup['lng'],
            pickup_address=pickup['address'],
            dropoff_lat=dropoff['lat'],
            dropoff_lng=dropoff['lng'],
            dropoff_address=dropoff['address'],
            fare=round(fare, 2),
            distance=round(distance, 2),
            duration=duration,
            status='requested'
        )
        
        db.session.add(trip)
        db.session.commit()
        
        # If notifyDrivers flag is set, find nearby online drivers
        if data.get('notifyDrivers'):
            online_drivers = Driver.query.filter_by(is_online=True, status='approved').all()
        
        return jsonify({
            'success': True,
            'message': 'Trip requested successfully',
            'data': trip.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'TRIP_CREATE_FAILED',
                'message': str(e)
            }
        }), 500

@trips_bp.route('', methods=['GET'])
@jwt_required()
def get_trips():
    """Get user's trips"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        status = request.args.get('status')
        
        # Build query based on user role
        if user.role == 'passenger':
            query = Trip.query.filter_by(passenger_id=user_id)
        elif user.role == 'driver':
            query = Trip.query.filter_by(driver_id=user_id)
        else:  # admin
            query = Trip.query
        
        if status:
            query = query.filter_by(status=status)
        
        # Get trips with eager loading for better performance
        trips = query.options(
            db.joinedload(Trip.passenger),
            db.joinedload(Trip.driver)
        ).order_by(Trip.created_at.desc()).limit(limit).offset((page-1)*limit).all()
        total = query.count()
        
        return jsonify({
            'success': True,
            'data': {
                'trips': [trip.to_dict() for trip in trips],
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': math.ceil(total / limit)
                }
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

@trips_bp.route('/<trip_id>/accept', methods=['PUT'])
@jwt_required()
def accept_trip(trip_id):
    """Driver accepts trip"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != 'driver':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Only drivers can accept trips'
                }
            }), 403
        
        trip = Trip.query.get(trip_id)
        
        if not trip:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'TRIP_NOT_FOUND',
                    'message': 'Trip not found'
                }
            }), 404
        
        if trip.status != 'requested':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': 'Trip is not available'
                }
            }), 400
        
        # Update trip
        trip.driver_id = user_id
        trip.status = 'accepted'
        trip.accepted_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Trip accepted',
            'data': trip.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'ACCEPT_FAILED',
                'message': str(e)
            }
        }), 500

@trips_bp.route('/<trip_id>/complete', methods=['PUT'])
@jwt_required()
def complete_trip(trip_id):
    """Complete trip"""
    try:
        user_id = get_jwt_identity()
        trip = Trip.query.get(trip_id)
        
        if not trip or trip.driver_id != user_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Unauthorized'
                }
            }), 403
        
        trip.status = 'completed'
        trip.completed_at = datetime.utcnow()
        # Update payment status based on config
        try:
            from models import Config
            auto_payment = Config.get_value('AUTO_COMPLETE_PAYMENT', 'true').lower() == 'true'
            trip.payment_status = 'paid' if auto_payment else 'pending'
        except:
            trip.payment_status = 'paid'  # Default behavior
        
        # Update driver stats
        driver = Driver.query.filter_by(user_id=user_id).first()
        if driver:
            driver.total_trips += 1
            driver.total_earnings += trip.fare
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Trip completed',
            'data': trip.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'COMPLETE_FAILED',
                'message': str(e)
            }
        }), 500

@trips_bp.route('/<trip_id>/rate', methods=['POST'])
@jwt_required()
def rate_trip(trip_id):
    """Rate completed trip"""
    try:
        user_id = get_jwt_identity()
        trip = Trip.query.get(trip_id)
        
        if not trip or trip.passenger_id != user_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Unauthorized'
                }
            }), 403
        
        data = request.json
        rating = data.get('rating')
        feedback = data.get('feedback', '')
        
        if not rating or rating < 1 or rating > 5:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_RATING',
                    'message': 'Rating must be between 1 and 5'
                }
            }), 400
        
        trip.rating = rating
        trip.feedback = feedback
        
        # Update driver rating
        if trip.driver_id:
            driver = Driver.query.filter_by(user_id=trip.driver_id).first()
            if driver:
                # Calculate new average rating efficiently
                avg_rating = db.session.query(db.func.avg(Trip.rating)).filter(
                    Trip.driver_id == trip.driver_id,
                    Trip.rating.isnot(None)
                ).scalar()
                
                driver.rating = round(float(avg_rating), 2) if avg_rating else 0
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Rating submitted',
            'data': trip.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'RATING_FAILED',
                'message': str(e)
            }
        }), 500

@trips_bp.route('/available', methods=['GET'])
@jwt_required()
def get_available_trips():
    """Get available trips for drivers"""
    try:
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
        
        # Get trips that are requested and not assigned with optimization
        trips = Trip.query.options(
            db.joinedload(Trip.passenger)
        ).filter_by(status='requested', driver_id=None).order_by(Trip.created_at.desc()).limit(20).all()
        
        return jsonify({
            'success': True,
            'data': [trip.to_dict() for trip in trips]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'FETCH_FAILED',
                'message': str(e)
            }
        }), 500