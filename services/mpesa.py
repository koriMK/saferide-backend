class MpesaService:
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        # Mock implementation for demo
        return {
            'success': True,
            'checkout_request_id': f'mock_{phone_number}_{amount}',
            'response_description': 'Mock STK Push initiated'
        }
    
    def query_stk_status(self, checkout_request_id):
        # Mock implementation for demo
        return {
            'success': True,
            'data': {
                'ResultCode': '0',
                'MpesaReceiptNumber': f'MOCK{checkout_request_id[-8:]}'
            }
        }