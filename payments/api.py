import requests
import base64
import json
import hashlib
import time
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from .models import TransactionLog


class MPesaAPI:
    """
    M-Pesa API integration for payment processing
    """
    
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.business_shortcode = settings.MPESA_BUSINESS_SHORT_CODE
        self.passkey = settings.MPESA_PASSKEY
        self.environment = settings.MPESA_ENVIRONMENT
        
        # API endpoints
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'
        
        self.access_token = None
        self.token_expiry = None
    
    def get_access_token(self):
        """Get M-Pesa access token"""
        if self.access_token and self.token_expiry and timezone.now() < self.token_expiry:
            return self.access_token
        
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        
        # Create Basic Auth header
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data.get('access_token')
            
            # Set token expiry (subtract 5 minutes for safety)
            expires_in = data.get('expires_in', 3600) - 300
            self.token_expiry = timezone.now() + timezone.timedelta(seconds=expires_in)
            
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            self.log_transaction('get_access_token', 'failed', str(e))
            raise Exception(f"Failed to get access token: {str(e)}")
    
    def generate_password(self, timestamp):
        """Generate M-Pesa API password"""
        password_string = f"{self.business_shortcode}{self.passkey}{timestamp}"
        return base64.b64encode(password_string.encode()).decode()
    
    def initiate_payment(self, phone_number, amount, payment_number, booking_number):
        """
        Initiate STK Push payment
        """
        try:
            access_token = self.get_access_token()
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = self.generate_password(timestamp)
            
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": f"{settings.BASE_URL}/api/payments/mpesa/callback/",
                "AccountReference": payment_number,
                "TransactionDesc": f"AgroHire Booking {booking_number}"
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ResponseCode') == '0':
                self.log_transaction('initiate_payment', 'success', result)
                return {
                    'success': True,
                    'MerchantRequestID': result.get('MerchantRequestID'),
                    'CheckoutRequestID': result.get('CheckoutRequestID'),
                    'ResponseCode': result.get('ResponseCode'),
                    'ResponseDescription': result.get('ResponseDescription'),
                    'CustomerMessage': result.get('CustomerMessage')
                }
            else:
                self.log_transaction('initiate_payment', 'failed', result)
                return {
                    'success': False,
                    'error': result.get('ResponseDescription', 'Payment initiation failed'),
                    'ResponseCode': result.get('ResponseCode')
                }
                
        except requests.exceptions.RequestException as e:
            self.log_transaction('initiate_payment', 'failed', str(e))
            return {
                'success': False,
                'error': f"Network error: {str(e)}"
            }
        except Exception as e:
            self.log_transaction('initiate_payment', 'failed', str(e))
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def process_refund(self, transaction_id, amount, phone_number):
        """
        Process refund for a transaction
        """
        try:
            access_token = self.get_access_token()
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = self.generate_password(timestamp)
            
            url = f"{self.base_url}/mpesa/reversal/v1/request"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "Initiator": "AgroHire",
                "SecurityCredential": self.generate_security_credential(),
                "CommandID": "TransactionReversal",
                "TransactionID": transaction_id,
                "Amount": int(amount),
                "ReceiverParty": phone_number,
                "RecieverIdentifierType": "11",  # MSISDN
                "ResultURL": f"{settings.BASE_URL}/api/payments/mpesa/refund-callback/",
                "QueueTimeOutURL": f"{settings.BASE_URL}/api/payments/mpesa/timeout/",
                "Remarks": "AgroHire refund",
                "Occasion": "Refund"
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ResponseCode') == '0':
                self.log_transaction('process_refund', 'success', result)
                return {
                    'success': True,
                    'TransID': result.get('TransactionID'),
                    'ResultCode': result.get('ResultCode'),
                    'ResultDesc': result.get('ResultDesc')
                }
            else:
                self.log_transaction('process_refund', 'failed', result)
                return {
                    'success': False,
                    'error': result.get('ResultDesc', 'Refund failed'),
                    'ResultCode': result.get('ResultCode')
                }
                
        except requests.exceptions.RequestException as e:
            self.log_transaction('process_refund', 'failed', str(e))
            return {
                'success': False,
                'error': f"Network error: {str(e)}"
            }
        except Exception as e:
            self.log_transaction('process_refund', 'failed', str(e))
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def generate_security_credential(self):
        """
        Generate security credential for API calls
        Note: This is a simplified version. In production, you should use proper encryption.
        """
        # This is a placeholder. In production, you need to implement proper encryption
        # as per M-Pesa API documentation
        return base64.b64encode("your_security_credential".encode()).decode()
    
    def verify_transaction(self, checkout_request_id):
        """
        Verify transaction status
        """
        try:
            access_token = self.get_access_token()
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = self.generate_password(timestamp)
            
            url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ResponseCode') == '0':
                self.log_transaction('verify_transaction', 'success', result)
                return {
                    'success': True,
                    'ResultCode': result.get('ResultCode'),
                    'ResultDesc': result.get('ResultDesc'),
                    'TransactionID': result.get('TransactionID'),
                    'Amount': result.get('Amount'),
                    'MpesaReceiptNumber': result.get('MpesaReceiptNumber')
                }
            else:
                self.log_transaction('verify_transaction', 'failed', result)
                return {
                    'success': False,
                    'error': result.get('ResultDesc', 'Transaction verification failed'),
                    'ResultCode': result.get('ResultCode')
                }
                
        except requests.exceptions.RequestException as e:
            self.log_transaction('verify_transaction', 'failed', str(e))
            return {
                'success': False,
                'error': f"Network error: {str(e)}"
            }
        except Exception as e:
            self.log_transaction('verify_transaction', 'failed', str(e))
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def log_transaction(self, action, status, data):
        """Log transaction details"""
        try:
            TransactionLog.objects.create(
                action=action,
                status=status,
                message=f"M-Pesa API {action}",
                data=data if isinstance(data, dict) else {'response': str(data)}
            )
        except Exception as e:
            # Log to console if database logging fails
            print(f"Failed to log transaction: {e}")


class MPesaCallbackHandler:
    """
    Handle M-Pesa callback responses
    """
    
    @staticmethod
    def handle_payment_callback(callback_data):
        """
        Handle STK Push callback
        """
        try:
            from .models import Payment
            
            # Extract callback data
            result_code = callback_data.get('ResultCode')
            result_desc = callback_data.get('ResultDesc')
            merchant_request_id = callback_data.get('MerchantRequestID')
            checkout_request_id = callback_data.get('CheckoutRequestID')
            
            # Find the payment
            try:
                payment = Payment.objects.get(
                    mpesa_merchant_request_id=merchant_request_id,
                    mpesa_checkout_request_id=checkout_request_id
                )
            except Payment.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Payment not found'
                }
            
            # Process the callback
            if result_code == '0':
                # Payment successful
                transaction_data = {
                    'TransID': callback_data.get('TransactionID'),
                    'ResultCode': result_code,
                    'ResultDesc': result_desc,
                    'Amount': callback_data.get('Amount'),
                    'MpesaReceiptNumber': callback_data.get('MpesaReceiptNumber'),
                    'TransactionDate': callback_data.get('TransactionDate')
                }
                
                payment.confirm_mpesa_payment(transaction_data)
                
                return {
                    'success': True,
                    'message': 'Payment confirmed successfully',
                    'payment_id': payment.id
                }
            else:
                # Payment failed
                payment.status = 'failed'
                payment.mpesa_result_code = result_code
                payment.mpesa_result_desc = result_desc
                payment.save()
                
                return {
                    'success': False,
                    'error': result_desc,
                    'payment_id': payment.id
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Callback processing error: {str(e)}"
            }
    
    @staticmethod
    def handle_refund_callback(callback_data):
        """
        Handle refund callback
        """
        try:
            from .models import Refund
            
            result_code = callback_data.get('ResultCode')
            result_desc = callback_data.get('ResultDesc')
            transaction_id = callback_data.get('TransactionID')
            
            # Find the refund
            try:
                refund = Refund.objects.get(
                    mpesa_transaction_id=transaction_id
                )
            except Refund.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Refund not found'
                }
            
            # Process the callback
            if result_code == '0':
                refund.status = 'completed'
                refund.mpesa_result_code = result_code
                refund.mpesa_result_desc = result_desc
                refund.save()
                
                return {
                    'success': True,
                    'message': 'Refund completed successfully',
                    'refund_id': refund.id
                }
            else:
                refund.status = 'failed'
                refund.mpesa_result_code = result_code
                refund.mpesa_result_desc = result_desc
                refund.save()
                
                return {
                    'success': False,
                    'error': result_desc,
                    'refund_id': refund.id
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Refund callback processing error: {str(e)}"
            }
