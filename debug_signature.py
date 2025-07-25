#!/usr/bin/env python3
"""
Debug script to test Bitso API signature generation
This helps verify the signature format matches Bitso's requirements
"""

import os
import sys
import logging
sys.path.append('src')

from bitso_api import BitsoAPI

# Set up debug logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def test_signature_generation():
    """Test signature generation with debug output"""
    print("=" * 60)
    print("Bitso API Signature Generation Test")
    print("=" * 60)
    
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please create it with your API credentials.")
        return
    
    try:
        # Create API instance with debug enabled
        api = BitsoAPI(debug=True)
        
        print(f"API Key: {api.api_key[:8]}...")
        print(f"Base URL: {api.base_url}")
        print()
        
        # Test signature generation for account_status endpoint
        print("Testing signature generation for /account_status:")
        print("-" * 40)
        
        headers = api._generate_signature('GET', '/account_status')
        
        print(f"Authorization Header: {headers['Authorization']}")
        print()
        
        # Test with a different endpoint
        print("Testing signature generation for /balance:")
        print("-" * 40)
        
        headers = api._generate_signature('GET', '/balance')
        
        print(f"Authorization Header: {headers['Authorization']}")
        print()
        
        print("✅ Signature generation test completed!")
        print("Check the debug output above for details.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_signature_generation()
