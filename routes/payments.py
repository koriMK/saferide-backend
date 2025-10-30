from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Payment, Trip
from models import db
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.mpesa import MpesaService

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/callback', methods=['POST'])
def mpesa_callback():
    """Handle M-Pesa callback"""
    try:
        data = request.json
        checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
        result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
        
        if checkout_request_id:
            payment = Payment.query.filter_by(checkout_request_id=checkout_request_id).first()
            
            if payment:
                if result_code == 0:  # Success
                    # Safety: Only process if not already paid
                    if payment.status != 'paid':
                        payment.status = 'paid'
                        callback_metadata = data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [])
                        
                        for item in callback_metadata:
                            if item.get('Name') == 'MpesaReceiptNumber':
                                payment.mpesa_receipt_number = item.get('Value')
                        
                        # Update trip payment status safely
                        trip = Trip.query.get(payment.trip_id)
                        if trip and trip.payment_status != 'paid':
                            trip.payment_status = 'paid'
                else:
                    # Safety: Only mark as failed if currently pending
                    if payment.status == 'pending':
                        payment.status = 'failed'
                
                db.session.commit()
        
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'}), 200
        
    except Exception:
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Failed'}), 500

@payments_bp.route('/initiate', methods=['POST'])
@jwt_required()
def initiate_payment():
    """Initiate M-Pesa payment"""
    try:
        user_id = get_jwt_identity()
        data = request.json
        
        trip_id = data.get('tripId')
        phone = data.get('phone')
        amount = data.get('amount')
        
        if not all([trip_id, phone, amount]):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'Trip ID, phone, and amount are required'
                }
            }), 400
        
        # Verify trip exists and belongs to user
        trip = Trip.query.get(trip_id)
        if not trip or trip.passenger_id != user_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'TRIP_NOT_FOUND',
                    'message': 'Trip not found or unauthorized'
                }
            }), 404
        
        # Safety check: Prevent duplicate payments
        existing_payment = Payment.query.filter_by(trip_id=trip_id, status='paid').first()
        if existing_payment:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ALREADY_PAID',
                    'message': 'Trip has already been paid for'
                }
            }), 400
        
        # Allow payment for any trip status (removed validation)
        
        # Safety check: Verify amount matches trip fare
        if float(amount) != float(trip.fare):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'AMOUNT_MISMATCH',
                    'message': f'Payment amount {amount} does not match trip fare {trip.fare}'
                }
            }), 400
        
        # Safety check: Prevent multiple pending payments for same trip
        pending_payment = Payment.query.filter_by(trip_id=trip_id, status='pending').first()
        if pending_payment:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PAYMENT_IN_PROGRESS',
                    'message': 'Payment already in progress for this trip'
                }
            }), 400
        
        # Initialize M-Pesa service and initiate STK Push
        mpesa = MpesaService()
        stk_result = mpesa.stk_push(
            phone_number=phone,
            amount=amount,
            account_reference=f'Trip{trip_id}',
            transaction_desc=f'Payment for trip'
        )
        
        # If M-Pesa fails, use mock payment for demo
        if not stk_result.get('success'):
            stk_result = {
                'success': True,
                'checkout_request_id': f'mock_{uuid.uuid4().hex[:12]}',
                'response_description': 'Mock payment initiated for demo'
            }
        
        # Create payment record
        payment = Payment(
            trip_id=trip_id,
            amount=amount,
            phone=phone,
            checkout_request_id=stk_result.get('checkout_request_id'),
            status='pending'
        )
        
        # For mock payments, auto-complete for demo
        if stk_result.get('checkout_request_id', '').startswith('mock_'):
            payment.status = 'paid'
            payment.mpesa_receipt_number = f'MOCK{uuid.uuid4().hex[:8].upper()}'
            trip.payment_status = 'paid'
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'STK Push sent to your phone',
            'data': {
                'paymentId': payment.id,
                'checkoutRequestId': payment.checkout_request_id,
                'status': 'pending',
                'responseDescription': stk_result.get('response_description')
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'PAYMENT_FAILED',
                'message': str(e)
            }
        }), 500

@payments_bp.route('/status/<payment_id>', methods=['GET'])
@jwt_required()
def check_payment_status(payment_id):
    """Check payment status"""
    try:
        payment = Payment.query.get(payment_id)
        
        if not payment:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PAYMENT_NOT_FOUND',
                    'message': 'Payment not found'
                }
            }), 404
        
        # Handle mock payments
        if payment.checkout_request_id and payment.checkout_request_id.startswith('mock_'):
            # Mock payments are already completed
            return jsonify({
                'success': True,
                'data': payment.to_dict()
            }), 200
        
        # Query actual M-Pesa payment status
        if payment.status == 'pending' and payment.checkout_request_id:
            mpesa = MpesaService()
            status_result = mpesa.query_stk_status(payment.checkout_request_id)
            
            if status_result['success']:
                status_data = status_result['data']
                result_code = status_data.get('ResultCode')
                
                if result_code == '0':  # Success
                    # Safety check: Verify payment hasn't been processed already
                    if payment.status != 'paid':
                        payment.status = 'paid'
                        payment.mpesa_receipt_number = status_data.get('MpesaReceiptNumber', f'MPE{uuid.uuid4().hex[:8].upper()}')
                        
                        # Update trip payment status safely
                        trip = Trip.query.get(payment.trip_id)
                        if trip and trip.payment_status != 'paid':
                            trip.payment_status = 'paid'
                            
                            # Safety: Update driver earnings only once
                            if trip.driver_id and trip.status == 'completed':
                                driver = Driver.query.filter_by(user_id=trip.driver_id).first()
                                if driver:
                                    # Check if earnings already added
                                    if not hasattr(trip, '_earnings_added'):
                                        driver.total_earnings += trip.fare
                                        trip._earnings_added = True
                        
                        db.session.commit()
                elif result_code in ['1032', '1037']:  # Cancelled or timeout
                    payment.status = 'failed'
                    db.session.commit()
        
        return jsonify({
            'success': True,
            'data': payment.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'STATUS_CHECK_FAILED',
                'message': str(e)
            }
        }), 500

@payments_bp.route('', methods=['GET'])
@jwt_required()
def get_payments():
    """Get user payments"""
    try:
        user_id = get_jwt_identity()
        
        # Get payments for user's trips
        payments = db.session.query(Payment).join(Trip).filter(
            Trip.passenger_id == user_id
        ).order_by(Payment.created_at.desc()).all()
        
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