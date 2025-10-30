from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Driver, Trip, Payment
from models import db
from datetime import datetime, timedelta
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

def admin_required():
    """Check if user is admin"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user and user.role == 'admin'

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get admin dashboard statistics"""
    try:
        if not admin_required():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ADMIN_REQUIRED',
                    'message': 'Admin access required'
                }
            }), 403
        
        # User stats
        total_users = User.query.count()
        total_passengers = User.query.filter_by(role='passenger').count()
        total_drivers = User.query.filter_by(role='driver').count()
        
        # Driver stats
        approved_drivers = Driver.query.filter_by(status='approved').count()
        pending_drivers = Driver.query.filter_by(status='pending').count()
        online_drivers = Driver.query.filter_by(status='approved', is_online=True).count()
        
        # Trip stats
        total_trips = Trip.query.count()
        completed_trips = Trip.query.filter_by(status='completed').count()
        active_trips = Trip.query.filter(
            Trip.status.in_(['requested', 'accepted', 'driving'])
        ).count()
        
        # Today's trips
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_trips = Trip.query.filter(Trip.created_at >= today_start).count()
        
        # Revenue stats
        total_revenue = db.session.query(func.sum(Trip.fare)).filter(
            Trip.status == 'completed',
            Trip.payment_status == 'paid'
        ).scalar() or 0
        
        today_revenue = db.session.query(func.sum(Trip.fare)).filter(
            Trip.status == 'completed',
            Trip.payment_status == 'paid',
            Trip.completed_at >= today_start
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'data': {
                'users': {
                    'total': total_users,
                    'passengers': total_passengers,
                    'drivers': total_drivers
                },
                'drivers': {
                    'total': total_drivers,
                    'approved': approved_drivers,
                    'pending': pending_drivers,
                    'online': online_drivers
                },
                'trips': {
                    'total': total_trips,
                    'completed': completed_trips,
                    'active': active_trips,
                    'today': today_trips
                },
                'revenue': {
                    'total': float(total_revenue),
                    'today': float(today_revenue)
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'STATS_FAILED',
                'message': str(e)
            }
        }), 500

@admin_bp.route('/drivers', methods=['GET'])
@jwt_required()
def get_all_drivers():
    """Get all drivers"""
    try:
        if not admin_required():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ADMIN_REQUIRED',
                    'message': 'Admin access required'
                }
            }), 403
        
        drivers = Driver.query.order_by(Driver.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': {
                'drivers': [driver.to_dict() for driver in drivers]
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

@admin_bp.route('/drivers/<driver_id>/approve', methods=['PUT'])
@jwt_required()
def approve_driver(driver_id):
    """Approve driver"""
    try:
        if not admin_required():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ADMIN_REQUIRED',
                    'message': 'Admin access required'
                }
            }), 403
        
        driver = Driver.query.get(driver_id)
        
        if not driver:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'DRIVER_NOT_FOUND',
                    'message': 'Driver not found'
                }
            }), 404
        
        driver.status = 'approved'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Driver approved',
            'data': driver.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'APPROVAL_FAILED',
                'message': str(e)
            }
        }), 500

@admin_bp.route('/trips', methods=['GET'])
@jwt_required()
def get_all_trips():
    """Get all trips"""
    try:
        if not admin_required():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ADMIN_REQUIRED',
                    'message': 'Admin access required'
                }
            }), 403
        
        trips = Trip.query.order_by(Trip.created_at.desc()).limit(50).all()
        
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

@admin_bp.route('/payments', methods=['GET'])
@jwt_required()
def get_all_payments():
    """Get all payments"""
    try:
        if not admin_required():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ADMIN_REQUIRED',
                    'message': 'Admin access required'
                }
            }), 403
        
        payments = Payment.query.order_by(Payment.created_at.desc()).limit(50).all()
        
        return jsonify({
            'success': True,
            'data': {
                'payments': [payment.to_dict() for payment in payments]
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

@admin_bp.route('/users/online', methods=['GET'])
@jwt_required()
def get_online_users():
    """Get all online users (drivers and passengers)"""
    try:
        if not admin_required():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ADMIN_REQUIRED',
                    'message': 'Admin access required'
                }
            }), 403
        
        # Get all approved drivers and passengers (simplified)
        online_drivers = db.session.query(User).join(Driver).filter(
            User.role == 'driver',
            Driver.status == 'approved'
        ).all()
        
        online_passengers = User.query.filter(
            User.role == 'passenger'
        ).all()
        
        return jsonify({
            'success': True,
            'data': {
                'drivers': [user.to_dict() for user in online_drivers],
                'passengers': [user.to_dict() for user in online_passengers],
                'summary': {
                    'totalDrivers': len(online_drivers),
                    'totalPassengers': len(online_passengers),
                    'totalUsers': len(online_drivers) + len(online_passengers)
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'ONLINE_USERS_FAILED',
                'message': str(e)
            }
        }), 500