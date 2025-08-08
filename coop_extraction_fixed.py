#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
import re

def extract_coop_data():
    """Extract data from Coop with JSON parsing fixes"""
    
    print("🔧 Coop Data Extraction (Fixed JSON Parsing)")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    url = "https://ereklamblad.se/Coop?publication=suVwNFKv"
    
    try:
        response = session.get(url, timeout=15)
        print(f"📊 Status: {response.status_code}, Length: {len(response.text)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
            print(f"🔍 Found {len(app_data_elements)} app-data elements")
            
            offer_ids = set()
            
            for i, element in enumerate(app_data_elements):
                print(f"\n📦 Processing app-data element {i+1}...")
                content = element.get_text().strip()
                print(f"   Length: {len(content)} chars")
                
                if content:
                    # Try multiple approaches to handle malformed JSON
                    
                    # Approach 1: Try to extract valid JSON segments
                    json_segments = []
                    
                    # Look for complete JSON objects
                    brace_level = 0
                    start_pos = 0
                    
                    for pos, char in enumerate(content):
                        if char == '{':
                            if brace_level == 0:
                                start_pos = pos
                            brace_level += 1
                        elif char == '}':
                            brace_level -= 1
                            if brace_level == 0:
                                # Found complete JSON object
                                json_segment = content[start_pos:pos+1]
                                json_segments.append(json_segment)
                    
                    print(f"   🔍 Found {len(json_segments)} JSON segments")
                    
                    # Parse each segment
                    for j, segment in enumerate(json_segments):
                        try:
                            data = json.loads(segment)
                            print(f"   ✅ Segment {j+1}: Valid JSON with {len(data) if isinstance(data, dict) else 'non-dict'} keys")
                            
                            # Extract offer IDs from this segment
                            def extract_ids_recursive(obj, path=""):
                                if isinstance(obj, dict):
                                    for key, value in obj.items():
                                        new_path = f"{path}.{key}" if path else key
                                        
                                        # Check for ID fields
                                        if key.lower() in ['id', 'offerid', 'offer_id'] and isinstance(value, str) and len(value) >= 10:
                                            offer_ids.add(value)
                                            print(f"      🎯 Found offer ID: {value} (at {new_path})")
                                        else:
                                            extract_ids_recursive(value, new_path)
                                            
                                elif isinstance(obj, list):
                                    for idx, item in enumerate(obj):
                                        new_path = f"{path}[{idx}]" if path else f"[{idx}]"
                                        extract_ids_recursive(item, new_path)
                            
                            extract_ids_recursive(data)
                            
                            # Also show some key information about this segment
                            if isinstance(data, dict):
                                interesting_keys = [key for key in data.keys() if any(term in key.lower() for term in ['offer', 'item', 'product', 'publication'])]
                                if interesting_keys:
                                    print(f"      🔑 Interesting keys: {interesting_keys}")
                            
                        except json.JSONDecodeError as e:
                            print(f"      ❌ Segment {j+1} JSON error: {e}")
                            continue
                    
                    # Approach 2: Regex extraction as fallback
                    if not offer_ids:
                        print("   🔍 Trying regex extraction...")
                        patterns = [
                            r'"id"\s*:\s*"([a-zA-Z0-9_-]{10,})"',
                            r'"offerId"\s*:\s*"([a-zA-Z0-9_-]{10,})"',
                            r'"offer_id"\s*:\s*"([a-zA-Z0-9_-]{10,})"',
                            r'"publicationId"\s*:\s*"([a-zA-Z0-9_-]{10,})"'
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                print(f"      🎯 Regex found {len(matches)} matches: {matches[:5]}...")
                                offer_ids.update(matches)
            
            print(f"\n📊 Summary:")
            print(f"   ✅ Total unique IDs found: {len(offer_ids)}")
            
            if offer_ids:
                print(f"\n📋 Found offer IDs:")
                for i, offer_id in enumerate(sorted(offer_ids), 1):
                    print(f"   {i:2d}. {offer_id}")
                
                # Test one offer
                test_id = list(offer_ids)[0]
                print(f"\n🧪 Testing offer: {test_id}")
                
                test_url = f"https://ereklamblad.se/Coop?publication=suVwNFKv&offer={test_id}"
                test_response = session.get(test_url, timeout=10)
                
                print(f"   📊 Test result: {test_response.status_code}")
                
                if test_response.status_code == 200:
                    test_soup = BeautifulSoup(test_response.text, 'html.parser')
                    title = test_soup.find('title')
                    if title:
                        clean_title = title.get_text().strip()
                        clean_title = re.sub(r'\s*från\s*Coop.*$', '', clean_title)
                        print(f"   📦 Product: {clean_title}")
                    
                    # Check for Swedish terms
                    content_lower = test_response.text.lower()
                    terms = ['pris', 'kr', 'erbjudande', 'coop']
                    found = [t for t in terms if t in content_lower]
                    print(f"   🇸🇪 Swedish terms: {found}")
                    
                    if len(found) >= 2:
                        print(f"   ✅ Looks like a valid Coop offer page!")
                        return list(offer_ids)
            
            if not offer_ids:
                print("❌ No offer IDs found - this might be a publication without individual offers")
                # Check if this is a catalog-style publication
                if 'katalog' in response.text.lower() or 'catalog' in response.text.lower():
                    print("   💡 This might be a catalog-style publication")
            
            return list(offer_ids)
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    coop_offers = extract_coop_data()
    
    if coop_offers:
        print(f"\n🎉 Success! Found {len(coop_offers)} Coop offers")
        print("✅ Coop integration is possible!")
    else:
        print(f"\n🤔 No individual offers found")
        print("   This might be a different type of publication (catalog vs individual offers)")
        print("   Still worth investigating further...")
