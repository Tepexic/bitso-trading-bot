#!/usr/bin/env python3
"""
Quick test script to verify Bitso API connection and basic functionality
"""

import os
import sys
sys.path.append('src')

from bitso_api import BitsoAPI
from analyzer import analyze_market_data

def test_api_connection():
    """Test basic API connection without authentication"""
    print("Testing Bitso API connection...")
    
    try:
        api = BitsoAPI()
        
        # Test public endpoint (no auth required)
        print("\n1. Testing public ticker endpoint...")
        ticker = api.get_ticker('eth_mxn')
        
        if ticker.get('success'):
            payload = ticker['payload']
            print(f"✅ Success! Current ETH price: {payload['last']} MXN")
            print(f"   Volume: {payload['volume']} ETH")
            print(f"   High: {payload['high']} MXN")
            print(f"   Low: {payload['low']} MXN")
        else:
            print(f"❌ Failed: {ticker}")
            return False
        
        # Test order book
        print("\n2. Testing order book endpoint...")
        order_book = api.get_order_book('eth_mxn')
        
        if order_book.get('success'):
            bids = order_book['payload']['bids'][:3]  # Top 3 bids
            asks = order_book['payload']['asks'][:3]  # Top 3 asks
            
            print("✅ Order book retrieved successfully!")
            print("   Top 3 Bids:", [f"{bid['price']} ({bid['amount']})" for bid in bids])
            print("   Top 3 Asks:", [f"{ask['price']} ({ask['amount']})" for ask in asks])
        else:
            print(f"❌ Order book failed: {order_book}")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_authenticated_endpoints():
    """Test authenticated endpoints (requires API credentials)"""
    print("\n3. Testing authenticated endpoints...")
    
    try:
        # Create API instance (will use staging environment based on .env)
        api = BitsoAPI(debug=False)
        
        print(f"Using API endpoint: {api.base_url}")
        
        # Test account status
        status = api.get_account_status()
        
        if status.get('success'):
            print("✅ Authentication successful!")
            print(f"   Account status: {status['payload']['status']}")
            return True
        else:
            print(f"❌ Authentication failed: {status}")
            if 'error' in status:
                error_code = status.get('error', {}).get('code', 'unknown')
                if error_code == 'invalid_auth' or error_code == '0201':
                    print("   Please check your API credentials in .env file")
                    print("   Make sure your credentials match the environment (staging vs production)")
            return False
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("   Please set BITSO_API_KEY and BITSO_API_SECRET in your .env file")
        return False
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Bitso Trading Bot - API Test Suite")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found.")
        print("   Copy .env.example to .env and add your API credentials")
        print("   You can still test public endpoints.\n")
    
    # Test public endpoints
    public_test = test_api_connection()
    
    if public_test:
        print("\n✅ Public API endpoints working correctly!")
        
        # Run market analysis
        print("\n" + "=" * 30)
        try:
            from bitso_api import BitsoAPI
            api = BitsoAPI()
            analyze_market_data(api)
        except Exception as e:
            print(f"Market analysis failed: {e}")
    
    # Test authenticated endpoints if credentials are available
    if os.path.exists('.env'):
        auth_test = test_authenticated_endpoints()
        
        if auth_test:
            print("\n✅ Authentication working correctly!")
            print("   Your bot is ready to trade!")
        else:
            print("\n❌ Authentication failed.")
            print("   Check your API credentials in .env file")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
