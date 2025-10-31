# SafeRide Backend - M-Pesa Integration Service
# Mock M-Pesa Daraja API implementation for development

class MpesaService:
    """M-Pesa payment service for STK Push and transaction queries"""
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK Push payment request (mock implementation)"""
        # Mock implementation for demo purposes
        # In production, this would call actual M-Pesa Daraja API
        return {
            'success': True,
            'checkout_request_id': f'mock_{phone_number}_{amount}',
            'response_description': 'Mock STK Push initiated'
        }
    
    def query_stk_status(self, checkout_request_id):
        """Query STK Push payment status (mock implementation)"""
        # Mock implementation for demo purposes
        # In production, this would query actual M-Pesa transaction status
        return {
            'success': True,
            'data': {
                'ResultCode': '0',  # 0 = success
                'MpesaReceiptNumber': f'MOCK{checkout_request_id[-8:]}'
            }
        }