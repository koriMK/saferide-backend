from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Trip, User, Driver, Config, db
from datetime import datetime
import math

trips_bp = Blueprint('trips', __name__)

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def calculate_fare(distance_km):
    try:
        base_fare = float(Config.query.filter_by(key='base_fare').first().value or 50)
        per_km_rate = float(Config.query.filter_by(key='per_km_rate').first().value or 25)
        minimum_fare = float(Config.query.filter_by(key='minimum_fare').first().value or 100)
        
        fare = base_fare + (distance_km * per_km_rate)
        return max(minimum_fare, round(fare, 2))
    except Exception:
        return max(100, round(50 + (distance_km * 25), 2))

@trips_bp.route('/request', methods=['POST'])
@jwt_required()
def request_trip():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'passenger':
            return jsonify({'success': False, 'error': {'code': 'PASSENGER_REQUIRED', 'message': 'Only passengers can request trips'}}), 403
        
        data = request.json
        pickup_lat = data.get('pickupLatitude')
        pickup_lng = data.get('pickupLongitude')
        pickup_address = data.get('pickupAddress')
        dest_lat = data.get('destinationLatitude')
        dest_lng = data.get('destinationLongitude')
        dest_address = data.get('destinationAddress')
        
        if not all([pickup_lat, pickup_lng, pickup_address, dest_lat, dest_lng, dest_address]):
            return jsonify({'success': False, 'error': {'code': 'MISSING_FIELDS', 'message': 'All location fields required'}}), 400
        
        distance = calculate_distance(pickup_lat, pickup_lng, dest_lat, dest_lng)
        fare = calculate_fare(distance)
        
        trip = Trip(
            passenger_id=user_id,
            pickup_latitude=pickup_lat,
            pickup_longitude=pickup_lng,
            pickup_address=pickup_address,
            destination_latitude=dest_lat,
            destination_longitude=dest_lng,
            destination_address=dest_address,
            fare=fare,
            distance=distance,
            status='requested'
        )
        
        db.session.add(trip)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Trip requested successfully',
            'data': {'trip': trip.to_dict()}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'TRIP_REQUEST_FAILED', 'message': str(e)}}), 500

@trips_bp.route('', methods=['GET'])
@jwt_required()
def get_trips():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role == 'passenger':
            trips = Trip.query.filter_by(passenger_id=user_id).order_by(Trip.created_at.desc()).all()
        elif user.role == 'driver':
            trips = Trip.query.filter_by(driver_id=user_id).order_by(Trip.created_at.desc()).all()
        else:
            trips = Trip.query.order_by(Trip.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': {'trips': [trip.to_dict() for trip in trips]}
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'FETCH_FAILED', 'message': str(e)}}), 500