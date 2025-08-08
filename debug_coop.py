#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re
import json

def debug_coop_page():
    """Debug Coop eReklamblad page structure"""
    
    # Setup session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    # Coop publication details
    publication_id = "suVwNFKv"
    base_url = "https://ereklamblad.se"
    coop_url = f"{base_url}/Coop?publication={publication_id}"
    
    print(f"🔍 Testing Coop eReklamblad page")
    print(f"🌐 Publication ID: {publication_id}")
    print(f"🌐 URL: {coop_url}")
    print("=" * 80)
    
    try:
        # Test main publication page
        print("📄 Testing main publication page...")
        response = session.get(coop_url, timeout=15)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📄 Content Length: {len(response.text)} characters")
        print(f"🗂️ Content Type: {response.headers.get('content-type', 'unknown')}")
        print()
        
        if response.status_code == 200 and response.text:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Check for app-data elements
            print("🔎 Searching for app-data elements...")
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
            print(f"   Found {len(app_data_elements)} app-data elements")
            
            offer_ids = set()
            
            for i, element in enumerate(app_data_elements):
                content = element.get_text().strip()
                print(f"   📦 Element {i+1}: {len(content)} chars")
                if content:
                    try:
                        # Try to parse as JSON
                        data = json.loads(content)
                        print(f"      ✅ Valid JSON")
                        
                        # Look for offer-related data
                        if isinstance(data, dict):
                            # Extract potential offer IDs
                            def find_offer_ids(obj, path=""):
                                if isinstance(obj, dict):
                                    for key, value in obj.items():
                                        if key.lower() in ['id', 'offerid', 'offer_id'] and isinstance(value, str) and len(value) >= 10:
                                            offer_ids.add(value)
                                            print(f"      🎯 Found offer ID: {value}")
                                        else:
                                            find_offer_ids(value, f"{path}.{key}" if path else key)
                                elif isinstance(obj, list):
                                    for item in obj:
                                        find_offer_ids(item, path)
                            
                            find_offer_ids(data)
                            
                            # Show some top-level keys
                            if isinstance(data, dict):
                                top_keys = list(data.keys())[:10]
                                print(f"      🔑 Top keys: {top_keys}")
                                
                    except json.JSONDecodeError:
                        print(f"      ❌ Not valid JSON")
                        # Look for ID patterns in raw text
                        id_patterns = [
                            r'"id"\s*:\s*"([a-zA-Z0-9_-]{10,})"',
                            r'"offerId"\s*:\s*"([a-zA-Z0-9_-]{10,})"',
                        ]
                        for pattern in id_patterns:
                            matches = re.findall(pattern, content)
                            if matches:
                                offer_ids.update(matches)
                                print(f"      🎯 Found IDs via regex: {matches[:5]}...")
            
            print()
            print(f"📋 Total unique offer IDs found: {len(offer_ids)}")
            
            if offer_ids:
                print("🎯 Sample offer IDs:")
                for i, offer_id in enumerate(list(offer_ids)[:10]):
                    print(f"   {i+1}. {offer_id}")
                
                # Test one offer URL
                test_offer = list(offer_ids)[0]
                print(f"\n🧪 Testing individual offer: {test_offer}")
                offer_url = f"{base_url}/Coop?publication={publication_id}&offer={test_offer}"
                
                offer_response = session.get(offer_url, timeout=10)
                print(f"   📡 Offer Status: {offer_response.status_code}")
                print(f"   📄 Offer Content Length: {len(offer_response.text)} chars")
                
                if offer_response.status_code == 200:
                    offer_soup = BeautifulSoup(offer_response.text, 'html.parser')
                    title = offer_soup.find('title')
                    if title:
                        print(f"   📄 Title: {title.get_text().strip()}")
                    
                    # Look for Swedish retail terms
                    swedish_terms = ['pris', 'erbjudande', 'kr', 'coop']
                    found_terms = [term for term in swedish_terms if term in offer_response.text.lower()]
                    print(f"   🇸🇪 Swedish terms found: {found_terms}")
            
            # 2. Check page title and basic structure
            print("\n🔎 Basic page analysis...")
            title = soup.find('title')
            if title:
                print(f"   📄 Title: {title.get_text().strip()}")
            
            # Check for Coop branding
            if "coop" in response.text.lower():
                print("   ✅ Page appears to be from Coop")
            else:
                print("   ❌ Page doesn't appear to be from Coop")
            
            # Check for Swedish retail terms
            swedish_terms = ['pris', 'erbjudande', 'kr', 'coop']
            found_terms = [term for term in swedish_terms if term in response.text.lower()]
            print(f"   🇸🇪 Swedish retail terms found: {found_terms}")
            
        else:
            print("❌ Failed to load page or empty content")
        
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_coop_page()
