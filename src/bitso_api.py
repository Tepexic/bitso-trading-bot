import os
import hmac
import hashlib
import time
import json
import requests
import random
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class BitsoAPI:
    """
    Bitso API client for interacting with the Bitso exchange
    """
    
    def __init__(self, debug: bool = False, use_staging: bool = None):
        self.api_key = os.getenv('BITSO_API_KEY')
        self.api_secret = os.getenv('BITSO_API_SECRET')
        
        # Determine whether to use staging environment
        if use_staging is None:
            use_staging = os.getenv('BITSO_USE_STAGING', 'True').lower() == 'true'
        
        # Use staging or production environment
        if use_staging:
            self.base_url = 'https://stage.bitso.com/api/v3'
            if debug:
                logger.debug("Using Bitso STAGING environment")
        else:
            # self.base_url = 'https://api.bitso.com/v3'
            self.base_url = 'https://bitso.com/api/v3'
            if debug:
                logger.debug("Using Bitso PRODUCTION environment")
            
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.debug = debug
        
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret must be set in environment variables")
    
    def _rate_limit(self):
        """Implement rate limiting to avoid hitting API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, method: str, endpoint: str, headers: Dict = None, data: str = None) -> Dict:
        """Make HTTP request with error handling and rate limiting"""
        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, data=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout error for {method} {endpoint}")
            return {"success": False, "error": {"message": "Request timeout"}}
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {method} {endpoint}")
            return {"success": False, "error": {"message": "Connection error"}}
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} for {method} {endpoint}")
            try:
                error_data = e.response.json()
                return error_data
            except:
                return {"success": False, "error": {"message": f"HTTP {e.response.status_code}"}}
        except Exception as e:
            logger.error(f"Unexpected error for {method} {endpoint}: {e}")
            return {"success": False, "error": {"message": str(e)}}
    
    def _generate_nonce_v2(self) -> str:
        """
        Generate Nonce v2 according to Bitso's new specification
        Nonce v2 is a number between 14 and 19 digits, formed by concatenating:
        - A 13-digit Epoch timestamp in milliseconds
        - A random salt (1 to 6 digits)
        
        We use 6-digit salt for maximum entropy as recommended by Bitso
        """
        # Get current timestamp in milliseconds (should be 13 digits)
        timestamp_ms = int(time.time() * 1000)
        timestamp_str = str(timestamp_ms)
        
        # Ensure timestamp is exactly 13 digits (pad with leading zeros if needed)
        timestamp_str = timestamp_str.zfill(13)
        
        # Generate 6-digit salt for maximum entropy (as recommended by Bitso)
        salt = random.randint(100000, 999999)
        salt_str = str(salt)
        
        # Concatenate timestamp + salt (should result in 19 digits total)
        nonce = timestamp_str + salt_str
        
        if self.debug:
            logger.debug(f"Generated nonce: {nonce} (length: {len(nonce)})")
        
        return nonce
    
    def _generate_signature(self, method: str, endpoint: str, body: str = '') -> Dict[str, str]:
        """
        Generate signature for authenticated requests
        
        According to Bitso docs, the signature is created from:
        nonce + HTTP method + request path + JSON payload
        
        Note: request path must include '/api/v3' prefix
        """
        nonce = self._generate_nonce_v2()
        
        # The request path must include the full path including /api/v3
        request_path = f"/api/v3{endpoint}"
        
        # Create the message to sign: nonce + method + path + body
        message = nonce + method + request_path + body
        
        if self.debug:
            logger.debug(f"Signature components:")
            logger.debug(f"  Nonce: {nonce}")
            logger.debug(f"  Method: {method}")
            logger.debug(f"  Request path: {request_path}")
            logger.debug(f"  Body: {body}")
            logger.debug(f"  Message to sign: {message}")
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if self.debug:
            logger.debug(f"  Generated signature: {signature}")
        
        return {
            'Authorization': f'Bitso {self.api_key}:{nonce}:{signature}',
            'Content-Type': 'application/json'
        }
    
    def get_ticker(self, book: str = 'eth_mxn') -> Dict:
        """Get ticker information for a specific book"""
        endpoint = f'/ticker?book={book}'
        return self._make_request('GET', endpoint)
    
    def get_order_book(self, book: str = 'eth_mxn') -> Dict:
        """Get order book for a specific book"""
        endpoint = f'/order_book?book={book}'
        return self._make_request('GET', endpoint)
    
    def get_available_books(self) -> List[Dict]:
        """Get all available trading books/pairs"""
        endpoint = '/available_books'
        response = self._make_request('GET', endpoint)
        return response.get('payload', [])
    
    def get_account_status(self) -> Dict:
        """Get account status (requires authentication)"""
        endpoint = '/account_status'
        headers = self._generate_signature('GET', endpoint)
        return self._make_request('GET', endpoint, headers)
    
    def get_balance(self) -> Dict:
        """Get account balance (requires authentication)"""
        endpoint = '/balance'
        headers = self._generate_signature('GET', endpoint)
        return self._make_request('GET', endpoint, headers)
    
    def place_order(self, book: str, side: str, order_type: str, major: Optional[float] = None, 
                   minor: Optional[float] = None, price: Optional[float] = None) -> Dict:
        """
        Place a trading order
        
        Args:
            book: Trading pair (e.g., 'eth_mxn')
            side: 'buy' or 'sell'
            order_type: 'market' or 'limit'
            major: Amount of crypto currency (e.g., ETH)
            minor: Amount of fiat currency (e.g., MXN)
            price: Price for limit orders
        """
        endpoint = '/orders'
        
        order_data = {
            'book': book,
            'side': side,
            'type': order_type
        }
        
        # Bitso requires either major or minor, not amount
        if major is not None:
            order_data['major'] = str(major)
        elif minor is not None:
            order_data['minor'] = str(minor)
        else:
            raise ValueError("Either major or minor amount must be specified")
        
        if order_type == 'limit' and price:
            order_data['price'] = str(price)
        
        body = json.dumps(order_data)
        headers = self._generate_signature('POST', endpoint, body)
        
        return self._make_request('POST', endpoint, headers, body)
    
    def get_open_orders(self) -> Dict:
        """Get all open orders"""
        endpoint = '/open_orders'
        headers = self._generate_signature('GET', endpoint)
        return self._make_request('GET', endpoint, headers)
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel a specific order"""
        endpoint = f'/orders/{order_id}'
        headers = self._generate_signature('DELETE', endpoint)
        return self._make_request('DELETE', endpoint, headers)
