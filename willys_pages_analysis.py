#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
import re
import time

def analyze_willys_pages():
    """Analyze individual pages of Willys publication"""
    
    print("📄 Willys Individual Pages Analysis")
    print("=" * 50)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    publication_id = "Hn02_ny6"
    base_url = f"https://ereklamblad.se/Willys?publication={publication_id}"
    
    # First, get publication info to determine page count
    print(f"📡 Getting publication info...")
    response = session.get(base_url, timeout=15)
    
    if response.status_code != 200:
        print(f"❌ Failed to load publication: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
    
    page_count = 0
    publication_data = None
    
    for element in app_data_elements:
        content = element.get_text().strip()
        
        # Extract JSON segments
        json_segments = []
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
                    json_segment = content[start_pos:pos+1]
                    json_segments.append(json_segment)
        
        for segment in json_segments:
            try:
                data = json.loads(segment)
                if isinstance(data, dict) and 'publication' in data:
                    publication_data = data['publication']
                    page_count = publication_data.get('pageCount', 0)
                    print(f"📊 Publication: {publication_data.get('name', 'Unknown')}")
                    print(f"📄 Total pages: {page_count}")
                    break
            except:
                continue
        
        if page_count > 0:
            break
    
    if page_count == 0:
        print(f"❌ Could not determine page count")
        return
    
    # Test different URL patterns for accessing individual pages
    print(f"\n🧪 Testing Page Access Patterns:")
    
    page_access_patterns = [
        lambda p: f"https://ereklamblad.se/Willys?publication={publication_id}&page={p}",
        lambda p: f"https://ereklamblad.se/Willys/{publication_id}/page/{p}",
        lambda p: f"https://ereklamblad.se/Willys?publication={publication_id}&pageNumber={p}",
        lambda p: f"https://ereklamblad.se/Willys/{publication_id}/{p}",
    ]
    
    successful_pattern = None
    test_page = 1
    
    for i, pattern_func in enumerate(page_access_patterns, 1):
        test_url = pattern_func(test_page)
        print(f"   Pattern {i}: {test_url}")
        
        try:
            test_response = session.get(test_url, timeout=10)
            print(f"      Status: {test_response.status_code}")
            
            if test_response.status_code == 200:
                # Check if it's actually a different page (not just redirected to main)
                if len(test_response.text) > 1000 and 'app-data' in test_response.text:
                    print(f"      ✅ Pattern works!")
                    successful_pattern = pattern_func
                    break
                else:
                    print(f"      ❌ Redirected or empty response")
            else:
                print(f"      ❌ Failed")
        
        except Exception as e:
            print(f"      💥 Error: {e}")
        
        time.sleep(1)  # Be nice to the server
    
    if not successful_pattern:
        print(f"\n❌ No successful page access pattern found")
        print(f"   Willys might not support direct page access")
        print(f"   Or it might require JavaScript rendering")
        return
    
    print(f"\n✅ Found working pattern! Analyzing pages...")
    
    # Analyze several pages to find offers
    pages_to_check = min(5, page_count)  # Check first 5 pages or all if less
    all_offers = []
    
    for page_num in range(1, pages_to_check + 1):
        print(f"\n📄 Analyzing Page {page_num}...")
        
        page_url = successful_pattern(page_num)
        
        try:
            page_response = session.get(page_url, timeout=10)
            
            if page_response.status_code == 200:
                page_soup = BeautifulSoup(page_response.text, 'html.parser')
                page_app_data = page_soup.find_all(id=lambda x: x and 'app-data' in x)
                
                print(f"   📦 App-data elements: {len(page_app_data)}")
                
                page_offers = []
                
                for element in page_app_data:
                    page_content = element.get_text().strip()
                    
                    # Look for offer-like patterns
                    offer_patterns = [
                        r'"name"\s*:\s*"([^"]{5,50})".*?"price"[^}]*"amount"\s*:\s*([0-9.]+)',
                        r'"title"\s*:\s*"([^"]{5,50})".*?"price"\s*:\s*([0-9.]+)',
                        r'"product"\s*:\s*"([^"]{5,50})".*?"kr"\s*:\s*([0-9.]+)',
                    ]
                    
                    for pattern in offer_patterns:
                        matches = re.findall(pattern, page_content, re.IGNORECASE | re.DOTALL)
                        for match in matches:
                            if len(match) == 2:
                                offer_name, offer_price = match
                                page_offers.append({
                                    'name': offer_name.strip(),
                                    'price': offer_price.strip(),
                                    'page': page_num,
                                    'source': 'regex_pattern'
                                })
                    
                    # Also try JSON parsing for structured data
                    json_segments = []
                    brace_level = 0
                    start_pos = 0
                    
                    for pos, char in enumerate(page_content):
                        if char == '{':
                            if brace_level == 0:
                                start_pos = pos
                            brace_level += 1
                        elif char == '}':
                            brace_level -= 1
                            if brace_level == 0:
                                json_segment = page_content[start_pos:pos+1]
                                json_segments.append(json_segment)
                    
                    for segment in json_segments:
                        try:
                            data = json.loads(segment)
                            if isinstance(data, dict):
                                # Look for offers in various possible locations
                                def find_offers_in_data(obj, path=""):
                                    offers = []
                                    if isinstance(obj, dict):
                                        for key, value in obj.items():
                                            if key.lower() in ['offers', 'products', 'items', 'deals']:
                                                if isinstance(value, list):
                                                    for item in value:
                                                        if isinstance(item, dict):
                                                            name = item.get('name', item.get('title', 'Unknown'))
                                                            price = item.get('price', item.get('amount', 'Unknown'))
                                                            offers.append({
                                                                'name': name,
                                                                'price': price,
                                                                'page': page_num,
                                                                'source': f'json_{key}',
                                                                'data': item
                                                            })
                                            elif isinstance(value, (dict, list)):
                                                offers.extend(find_offers_in_data(value, f"{path}.{key}" if path else key))
                                    elif isinstance(obj, list):
                                        for i, item in enumerate(obj):
                                            offers.extend(find_offers_in_data(item, f"{path}[{i}]"))
                                    return offers
                                
                                structured_offers = find_offers_in_data(data)
                                page_offers.extend(structured_offers)
                        
                        except json.JSONDecodeError:
                            continue
                
                print(f"   🛍️ Offers found: {len(page_offers)}")
                
                if page_offers:
                    # Show first few offers from this page
                    for i, offer in enumerate(page_offers[:3], 1):
                        print(f"      {i}. {offer['name']} - {offer['price']} ({offer['source']})")
                    
                    all_offers.extend(page_offers)
                else:
                    print(f"      ❌ No offers found on this page")
                    
                    # Debug: show some content to understand the structure
                    if page_app_data:
                        sample_content = page_app_data[0].get_text()[:500]
                        print(f"      📝 Sample content: {sample_content[:200]}...")
            
            else:
                print(f"   ❌ Failed to load page {page_num}: {page_response.status_code}")
        
        except Exception as e:
            print(f"   💥 Error loading page {page_num}: {e}")
        
        time.sleep(1)  # Be respectful to the server
    
    # Summary
    print(f"\n📊 Analysis Summary:")
    print(f"   📄 Pages analyzed: {pages_to_check}")
    print(f"   🛍️ Total offers found: {len(all_offers)}")
    
    if all_offers:
        print(f"\n📋 Sample Offers:")
        unique_offers = {}
        for offer in all_offers:
            key = f"{offer['name']}_{offer['price']}"
            if key not in unique_offers:
                unique_offers[key] = offer
        
        for i, (key, offer) in enumerate(list(unique_offers.items())[:10], 1):
            print(f"   {i}. {offer['name']} - {offer['price']} (Page {offer['page']})")
        
        # Determine structure type
        sources = [offer['source'] for offer in all_offers]
        json_sources = [s for s in sources if s.startswith('json_')]
        
        if json_sources:
            print(f"\n✅ Willys uses structured JSON data")
            print(f"   📊 JSON sources found: {set(json_sources)}")
            return all_offers, "json_structured"
        elif len(all_offers) > 0:
            print(f"\n✅ Willys offers found via pattern matching")
            return all_offers, "pattern_based"
        else:
            print(f"\n❓ Offers found but structure unclear")
            return all_offers, "unknown_structure"
    
    else:
        print(f"\n❌ No offers found")
        print(f"   This might require JavaScript rendering")
        print(f"   Or the page structure is different than expected")
        return [], "no_offers"

if __name__ == "__main__":
    offers, structure_type = analyze_willys_pages()
    
    print(f"\n🎯 Final Analysis:")
    print(f"   🛍️ Offers: {len(offers)}")
    print(f"   🏗️ Structure: {structure_type}")
    
    if offers:
        print(f"✅ Successfully analyzed Willys page structure!")
        print(f"   Ready to integrate into universal scraper")
    else:
        print(f"❌ Unable to extract offers from pages")
        print(f"   May need browser-based approach")
