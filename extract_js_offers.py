#!/usr/bin/env python3

import json
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def extract_offers_from_javascript():
    """Extract offers from JavaScript content in Willys page"""
    
    print("🔍 Extracting Offers from JavaScript")
    print("=" * 50)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        publication_id = "Hn02_ny6"
        url = f"https://ereklamblad.se/Willys?publication={publication_id}"
        
        print(f"📡 Loading: {url}")
        driver.get(url)
        
        # Wait for dynamic content
        print("⏳ Waiting for JavaScript to load...")
        time.sleep(12)
        
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print(f"📊 Page loaded: {len(html_content):,} chars")
        
        # Find all script tags
        script_tags = soup.find_all('script')
        print(f"📜 Found {len(script_tags)} script tags")
        
        all_offers = []
        
        for i, script in enumerate(script_tags):
            if script.string:
                script_content = script.string.strip()
                
                if len(script_content) > 500:  # Only check substantial scripts
                    print(f"\n🔍 Analyzing script {i+1} ({len(script_content):,} chars)")
                    
                    # Look for offer-related keywords
                    offer_keywords = ['offer', 'product', 'item', 'price', 'amount']
                    keyword_count = sum(script_content.lower().count(kw) for kw in offer_keywords)
                    
                    if keyword_count > 5:  # Script contains significant offer-related content
                        print(f"   🎯 Found {keyword_count} offer-related keywords")
                        
                        # Try different methods to extract JSON data
                        offers_extracted = []
                        
                        # Method 1: Look for JSON objects in the script
                        json_patterns = [
                            r'({[^{}]*"(?:name|title)"[^{}]*"(?:price|amount)"[^{}]*})',
                            r'(\[{[^}]*"(?:name|title)"[^}]*}[^]]*\])',
                            r'({[^{}]*"(?:price|amount)"[^{}]*"(?:name|title)"[^{}]*})',
                        ]
                        
                        for pattern in json_patterns:
                            matches = re.findall(pattern, script_content, re.IGNORECASE | re.DOTALL)
                            for match in matches:
                                try:
                                    data = json.loads(match)
                                    if isinstance(data, dict):
                                        offers_extracted.append(data)
                                    elif isinstance(data, list):
                                        offers_extracted.extend([item for item in data if isinstance(item, dict)])
                                except json.JSONDecodeError:
                                    continue
                        
                        # Method 2: Look for variable assignments containing offer data
                        var_patterns = [
                            r'var\s+\w+\s*=\s*(\{[^;]+\})',
                            r'const\s+\w+\s*=\s*(\{[^;]+\})',
                            r'let\s+\w+\s*=\s*(\{[^;]+\})',
                            r'window\.\w+\s*=\s*(\{[^;]+\})',
                        ]
                        
                        for pattern in var_patterns:
                            matches = re.findall(pattern, script_content, re.IGNORECASE | re.DOTALL)
                            for match in matches:
                                if any(kw in match.lower() for kw in offer_keywords):
                                    try:
                                        data = json.loads(match)
                                        if isinstance(data, dict):
                                            offers_extracted.append(data)
                                    except json.JSONDecodeError:
                                        continue
                        
                        # Method 3: Look for specific eReklamblad data structures
                        ereklamblad_patterns = [
                            r'"offers"\s*:\s*(\[[^\]]+\])',
                            r'"products"\s*:\s*(\[[^\]]+\])',
                            r'"items"\s*:\s*(\[[^\]]+\])',
                            r'"catalog"\s*:\s*(\{[^}]+\})',
                        ]
                        
                        for pattern in ereklamblad_patterns:
                            matches = re.findall(pattern, script_content, re.IGNORECASE | re.DOTALL)
                            for match in matches:
                                try:
                                    data = json.loads(match)
                                    if isinstance(data, list):
                                        offers_extracted.extend([item for item in data if isinstance(item, dict)])
                                    elif isinstance(data, dict):
                                        offers_extracted.append(data)
                                except json.JSONDecodeError:
                                    continue
                        
                        # Method 4: Extract large JSON blocks and search within them
                        large_json_pattern = r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})'
                        large_matches = re.findall(large_json_pattern, script_content)
                        
                        for match in large_matches:
                            if len(match) > 200 and any(kw in match.lower() for kw in offer_keywords):
                                try:
                                    data = json.loads(match)
                                    if isinstance(data, dict):
                                        # Search within this JSON for offers
                                        nested_offers = extract_offers_from_nested_json(data)
                                        if nested_offers:
                                            offers_extracted.extend(nested_offers)
                                except json.JSONDecodeError:
                                    continue
                        
                        if offers_extracted:
                            print(f"   ✅ Extracted {len(offers_extracted)} potential offers")
                            all_offers.extend(offers_extracted)
                            
                            # Show samples
                            for j, offer in enumerate(offers_extracted[:3], 1):
                                offer_name = offer.get('name', offer.get('title', 'Unknown'))
                                offer_price = offer.get('price', offer.get('amount', 'No price'))
                                print(f"      {j}. {offer_name} - {offer_price}")
                        else:
                            print(f"   ❌ No offers extracted despite keywords")
                    else:
                        print(f"   ➖ Only {keyword_count} keywords - skipping")
        
        print(f"\n📊 Final Results:")
        print(f"   🛍️ Total offers found: {len(all_offers)}")
        
        if all_offers:
            print(f"\n📋 Sample Offers:")
            unique_offers = {}
            for offer in all_offers:
                # Create a unique key based on name and price
                name = str(offer.get('name', offer.get('title', 'Unknown')))
                price = str(offer.get('price', offer.get('amount', 'Unknown')))
                key = f"{name}_{price}"
                
                if key not in unique_offers:
                    unique_offers[key] = offer
            
            for i, (key, offer) in enumerate(list(unique_offers.items())[:10], 1):
                name = offer.get('name', offer.get('title', 'Unknown'))
                price = offer.get('price', offer.get('amount', 'No price'))
                print(f"   {i}. {name} - {price}")
            
            return list(unique_offers.values())
        
        return []
    
    finally:
        driver.quit()
        print("🧹 Browser closed")

def extract_offers_from_nested_json(data, path=""):
    """Recursively extract offers from nested JSON data"""
    offers = []
    
    if isinstance(data, dict):
        # Check if this dict looks like an offer
        if any(key in data for key in ['name', 'title']) and any(key in data for key in ['price', 'amount']):
            offers.append(data)
        
        # Look for offers in known keys
        offer_keys = ['offers', 'products', 'items', 'deals']
        for key in offer_keys:
            if key in data and isinstance(data[key], list):
                for item in data[key]:
                    if isinstance(item, dict):
                        offers.append(item)
        
        # Recurse into nested objects
        if len(path.split('.')) < 3:  # Limit recursion depth
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    nested_offers = extract_offers_from_nested_json(value, f"{path}.{key}" if path else key)
                    offers.extend(nested_offers)
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                # Check if list item looks like an offer
                if any(key in item for key in ['name', 'title']) and any(key in item for key in ['price', 'amount']):
                    offers.append(item)
                else:
                    nested_offers = extract_offers_from_nested_json(item, f"{path}[{i}]")
                    offers.extend(nested_offers)
    
    return offers

if __name__ == "__main__":
    offers = extract_offers_from_javascript()
    
    if offers:
        print(f"\n🎯 SUCCESS: Found {len(offers)} unique offers!")
        print(f"📋 Willys browser scraping is working!")
    else:
        print(f"\n❌ No offers found in JavaScript content")
        print(f"📋 May need to investigate page interaction or API calls")
