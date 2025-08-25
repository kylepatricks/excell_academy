# finance/paystack_utils.py
import requests
from django.conf import settings


class PaystackAPI:
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.public_key = settings.PAYSTACK_PUBLIC_KEY
        self.base_url = settings.PAYSTACK_BASE_URL
        
    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
    
    def initialize_transaction(self, email, amount, reference, callback_url, metadata=None):
        """Initialize a Paystack transaction"""
        url = f"{self.base_url}/transaction/initialize"
        
        payload = {
            'email': email,
            'amount': int(amount), 
            'reference': reference,
            'callback_url': callback_url,
            'metadata': metadata or {}
        }
        
        response = requests.post(url, json=payload, headers=self.get_headers())
        return response.json()
    
    def verify_transaction(self, reference):
        """Verify a Paystack transaction"""
        url = f"{self.base_url}/transaction/verify/{reference}"
        
        response = requests.get(url, headers=self.get_headers())
        return response.json()
    
    def create_transfer_recipient(self, name, account_number, bank_code, currency='GHS'):
        """Create transfer recipient for refunds"""
        url = f"{self.base_url}/transferrecipient"
        
        payload = {
            'type': 'nuban',
            'name': name,
            'account_number': account_number,
            'bank_code': bank_code,
            'currency': currency
        }
        
        response = requests.post(url, json=payload, headers=self.get_headers())
        return response.json()
    
    def initiate_transfer(self, amount, recipient_code, reason):
        """Initiate transfer (for refunds)"""
        url = f"{self.base_url}/transfer"
        
        payload = {
            'source': 'balance',
            'amount': int(amount),
            'recipient': recipient_code,
            'reason': reason
        }
        
        response = requests.post(url, json=payload, headers=self.get_headers())
        return response.json()

# Create a singleton instance
paystack_api = PaystackAPI()