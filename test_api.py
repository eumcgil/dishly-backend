#!/usr/bin/env python3
"""
Test script for the Dishly.pro Recipe Parser API
"""

import requests
import json
import sys
from typing import Dict, Any

def test_health_endpoint(base_url: str) -> bool:
    """Test the health endpoint"""
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_root_endpoint(base_url: str) -> bool:
    """Test the root endpoint"""
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            print("✅ Root endpoint working")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def test_parse_endpoint(base_url: str, test_url: str) -> bool:
    """Test the parse endpoint with a recipe URL"""
    try:
        payload = {"url": test_url}
        response = requests.post(
            f"{base_url}/parse",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            recipe = data.get("recipe", {})
            
            print("✅ Parse endpoint working")
            print(f"   Recipe: {recipe.get('title', 'No title')}")
            print(f"   Ingredients: {len(recipe.get('ingredients', []))} items")
            print(f"   Instructions: {len(recipe.get('instructions', []))} steps")
            print(f"   Source: {recipe.get('source_name', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Parse endpoint failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Parse endpoint error: {e}")
        return False

def main():
    """Run all tests"""
    base_url = "http://localhost:8000"
    
    # Test URLs (known to work with recipe-scrapers)
    test_urls = [
        "https://www.allrecipes.com/recipe/213742/chewy-chocolate-chip-cookies/",
        "https://www.foodnetwork.com/recipes/alton-brown/the-chewy-recipe-1909046",
        "https://www.tasteofhome.com/recipes/soft-chewy-chocolate-chip-cookies/",
    ]
    
    print("🧪 Testing Dishly.pro Recipe Parser API")
    print("=" * 50)
    
    # Test basic endpoints
    health_ok = test_health_endpoint(base_url)
    root_ok = test_root_endpoint(base_url)
    
    if not (health_ok and root_ok):
        print("\n❌ Basic endpoints failed. Make sure the server is running.")
        sys.exit(1)
    
    # Test parse endpoint with different URLs
    parse_success = False
    for test_url in test_urls:
        print(f"\n🔍 Testing with: {test_url}")
        if test_parse_endpoint(base_url, test_url):
            parse_success = True
            break
        print("   Trying next URL...")
    
    if parse_success:
        print("\n🎉 All tests passed! API is working correctly.")
    else:
        print("\n⚠️  Parse endpoint failed with all test URLs.")
        print("   This might be due to network issues or website changes.")
    
    print("\n📋 API Endpoints:")
    print(f"   Health: {base_url}/health")
    print(f"   Parse:  {base_url}/parse")
    print(f"   Docs:   {base_url}/docs")

if __name__ == "__main__":
    main()
