#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re
import json

def debug_offer_page():
    """Debug the actual content of offer pages"""
    
    # Setup session like scraper - but fix compression issue
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
        # Remove Accept-Encoding to let requests handle it automatically
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    test_offer = "em9yvCtQ7djrVR83KsdMP"
    url = f"https://ereklamblad.se/ICA-Maxi-Stormarknad?publication=5X0fxUgs&offer={test_offer}"
    
    print(f"🔍 Debugging offer page: {test_offer}")
    print(f"🌐 URL: {url}")
    print("=" * 80)
    
    try:
        # Make request with automatic decompression
        response = session.get(url, timeout=15)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📄 Content Length: {len(response.text)} characters")
        print(f"🗂️ Content Type: {response.headers.get('content-type', 'unknown')}")
        print(f"🗜️ Content Encoding: {response.headers.get('content-encoding', 'none')}")
        print()
        
        if response.status_code == 200 and response.text:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Check for app-data elements
            print("🔎 Searching for app-data elements...")
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
            print(f"   Found {len(app_data_elements)} app-data elements")
            
            for i, element in enumerate(app_data_elements):
                content = element.get_text().strip()
                print(f"   📦 Element {i+1}: {len(content)} chars")
                if content:
                    try:
                        # Try to parse as JSON
                        data = json.loads(content)
                        print(f"      ✅ Valid JSON with keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
                        
                        # Look for offer-related data
                        if isinstance(data, dict):
                            for key in ['offers', 'offer', 'product', 'item', 'data']:
                                if key in data:
                                    print(f"      🎯 Found key: {key}")
                    except json.JSONDecodeError:
                        print(f"      ❌ Not valid JSON")
                        # Show first 200 chars
                        preview = content[:200] + "..." if len(content) > 200 else content
                        print(f"      📝 Content preview: {preview}")
            
            print()
            
            # 2. Check for Next.js data
            print("🔎 Searching for Next.js data...")
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data:
                try:
                    data = json.loads(next_data.get_text())
                    print(f"   ✅ Found Next.js data with keys: {list(data.keys())}")
                except:
                    print(f"   ❌ Next.js data found but couldn't parse")
            else:
                print(f"   ❌ No Next.js data found")
            
            print()
            
            # 3. Look for any script tags with data
            print("🔎 Searching for script tags with data...")
            scripts = soup.find_all('script')
            data_scripts = 0
            for script in scripts:
                if script.string and len(script.string.strip()) > 100:
                    content = script.string.strip()
                    if any(keyword in content.lower() for keyword in ['offer', 'product', 'price', 'data']):
                        data_scripts += 1
                        print(f"   📜 Script {data_scripts}: {len(content)} chars")
                        # Look for JSON-like patterns
                        if '{' in content and '}' in content:
                            print(f"      🔍 Contains JSON-like structure")
                            # Try to extract offer ID
                            if test_offer in content:
                                print(f"      🎯 Contains our offer ID!")
            
            print(f"   Found {data_scripts} potentially relevant scripts")
            print()
            
            # 4. Check page title and basic structure
            print("🔎 Basic page analysis...")
            title = soup.find('title')
            if title:
                print(f"   📄 Title: {title.get_text().strip()}")
            
            # Look for any elements containing the offer ID
            elements_with_offer_id = soup.find_all(text=re.compile(test_offer, re.IGNORECASE))
            print(f"   🔍 Elements containing offer ID: {len(elements_with_offer_id)}")
            
            # Check if this looks like the expected page structure
            if "ereklamblad" in response.text.lower():
                print("   ✅ Page appears to be from eReklamblad")
            else:
                print("   ❌ Page doesn't appear to be from eReklamblad")
            
            # Check for common Swedish retail terms
            swedish_terms = ['pris', 'erbjudande', 'kr', 'ica', 'maxi']
            found_terms = [term for term in swedish_terms if term in response.text.lower()]
            print(f"   🇸🇪 Swedish retail terms found: {found_terms}")
            
            print()
            
            # 5. Show sample content for analysis
            print("� Sample content analysis...")
            print(f"   First 500 characters:")
            print("-" * 60)
            print(response.text[:500])
            print("-" * 60)
            
            # Check if this might be a redirect or different page
            if len(response.text) < 10000:  # Suspiciously small for a full page
                print("   ⚠️ Page content seems unusually small")
            
            # Look for any mention of the publication ID
            if "5X0fxUgs" in response.text:
                print("   ✅ Contains publication ID")
            else:
                print("   ❌ Missing publication ID")
            
            # Check response headers for clues
            print()
            print("📡 Response headers:")
            for key, value in response.headers.items():
                if key.lower() in ['location', 'refresh', 'set-cookie', 'server']:
                    print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_offer_page()
