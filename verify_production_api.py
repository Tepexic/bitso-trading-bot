#!/usr/bin/env python3
"""
Bitso Production API Verification Script
Helps diagnose 401 authentication issues with production credentials
"""

import os
import requests
import hmac
import hashlib
import time
import json
from dotenv import load_dotenv

load_dotenv()

def generate_nonce_v2():
    """Generate nonce in the exact format required by Bitso"""
    # Get current timestamp in milliseconds (should be 13 digits)
    timestamp_ms = int(time.time() * 1000)
    timestamp_str = str(timestamp_ms)
    
    # Ensure timestamp is exactly 13 digits (pad with leading zeros if needed)
    timestamp_str = timestamp_str.zfill(13)
    
    # Generate 6-digit salt for maximum entropy (as recommended by Bitso)
    import random
    salt = random.randint(100000, 999999)
    salt_str = str(salt)
    
    # Concatenate timestamp + salt (should result in 19 digits total)
    nonce = timestamp_str + salt_str
    
    return nonce

def generate_signature(api_secret, nonce, method, request_path, body=""):
    """Generate HMAC-SHA256 signature for Bitso API"""
    message = f"{nonce}{method}{request_path}{body}"
    signature = hmac.new(
        api_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_production_credentials():
    """Test production API credentials with detailed debugging"""
    
    print("=" * 60)
    print("Bitso Production API Credential Verification")
    print("=" * 60)
    
    # Get credentials
    api_key = os.getenv('BITSO_API_KEY')
    api_secret = os.getenv('BITSO_API_SECRET')
    use_staging = os.getenv('BITSO_USE_STAGING', 'True').lower() == 'true'
    
    if not api_key or not api_secret:
        print("❌ Missing API credentials in .env file")
        return False
    
    # Check environment
    if use_staging:
        base_url = 'https://stage.bitso.com/api/v3'
        print("🟡 WARNING: BITSO_USE_STAGING=True - using staging environment")
        print("   If you want to test production, set BITSO_USE_STAGING=False")
    else:
        base_url = 'https://api.bitso.com/v3'
        print("✅ Using PRODUCTION environment")
    
    print(f"API Key: {api_key[:8]}...")
    print(f"Base URL: {base_url}")
    print()
    
    # Test 1: Basic account status check
    print("Test 1: Account Status Check")
    print("-" * 30)
    
    endpoint = '/account_status'
    url = f"{base_url}{endpoint}"
    method = 'GET'
    
    # Generate authentication
    nonce = generate_nonce_v2()
    signature = generate_signature(api_secret, nonce, method, f"/api/v3{endpoint}")
    
    headers = {
        'Authorization': f'Bitso {api_key}:{nonce}:{signature}',
        'Content-Type': 'application/json'
    }
    
    print(f"Request URL: {url}")
    print(f"Nonce: {nonce} (length: {len(nonce)})")
    print(f"Signature: {signature}")
    print()
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                account_status = data['payload']['status']
                print(f"✅ Account Status: {account_status}")
                return True
            else:
                print(f"❌ API Error: {data}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            
            # Additional debugging for 401 errors
            if response.status_code == 401:
                print("\n🔍 401 Troubleshooting:")
                print("1. Check that your API key has the correct permissions")
                print("2. Verify your account is fully verified for production")
                print("3. Make sure the API key wasn't generated with IP restrictions")
                print("4. Check if your API key has trading permissions enabled")
                
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return False

def main():
    """Main verification process"""
    if test_production_credentials():
        print("\n🎉 Production API credentials are working!")
        print("You can now use the trading bot with production environment.")
    else:
        print("\n❌ Production API authentication failed.")
        print("\n📋 Next Steps:")
        print("1. Log into your Bitso account")
        print("2. Go to API section")
        print("3. Check your API key permissions:")
        print("   - Make sure 'View account status' is enabled")
        print("   - Make sure 'View balance' is enabled") 
        print("   - For trading, ensure 'Place orders' is enabled")
        print("4. If needed, generate a new API key with full permissions")
        print("5. Make sure your account is fully verified for production trading")

if __name__ == "__main__":
    main()
