#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
import re

def analyze_willys_catalog():
    """Analyze Willys catalog pages structure"""
    
    print("📖 Willys Catalog Structure Analysis")
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
    url = f"https://ereklamblad.se/Willys?publication={publication_id}"
    
    print(f"📡 Accessing publication: {publication_id}")
    
    response = session.get(url, timeout=15)
    print(f"📊 Status: {response.status_code}, Length: {len(response.text)}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
        
        pages_found = []
        spreads_found = []
        
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
                    
                    if isinstance(data, dict):
                        # Look for publication details
                        if 'publication' in data:
                            pub_data = data['publication']
                            print(f"\n📚 Publication Details:")
                            print(f"   📋 ID: {pub_data.get('publicId', 'Unknown')}")
                            print(f"   📝 Name: {pub_data.get('name', 'Unknown')}")
                            print(f"   ⏰ Valid until: {pub_data.get('validUntil', 'Unknown')}")
                            
                            # Look for pages/spreads in publication
                            if 'pages' in pub_data:
                                pages = pub_data['pages']
                                print(f"   📄 Pages: {len(pages) if isinstance(pages, list) else type(pages)}")
                                
                                if isinstance(pages, list) and pages:
                                    print(f"   🔍 Analyzing pages structure...")
                                    
                                    for i, page in enumerate(pages[:5]):  # First 5 pages
                                        if isinstance(page, dict):
                                            page_id = page.get('id', page.get('pageId', f'page_{i}'))
                                            page_number = page.get('pageNumber', page.get('number', i))
                                            
                                            print(f"      📃 Page {i+1}: ID={page_id}, Number={page_number}")
                                            
                                            pages_found.append({
                                                'id': page_id,
                                                'number': page_number,
                                                'data': page
                                            })
                                            
                                            # Look for offers within this page
                                            if 'offers' in page:
                                                offers = page['offers']
                                                print(f"         🛍️ Offers: {len(offers) if isinstance(offers, list) else type(offers)}")
                                            
                                            # Check all keys in the page
                                            page_keys = list(page.keys())
                                            interesting_keys = [k for k in page_keys if any(term in k.lower() for term in ['offer', 'item', 'product', 'deal'])]
                                            if interesting_keys:
                                                print(f"         🎯 Interesting keys: {interesting_keys}")
                            
                            # Look for spreads
                            if 'spreads' in pub_data:
                                spreads = pub_data['spreads']
                                print(f"   📖 Spreads: {len(spreads) if isinstance(spreads, list) else type(spreads)}")
                                
                                if isinstance(spreads, list) and spreads:
                                    for i, spread in enumerate(spreads[:3]):  # First 3 spreads
                                        if isinstance(spread, dict):
                                            spread_id = spread.get('id', f'spread_{i}')
                                            print(f"      📖 Spread {i+1}: ID={spread_id}")
                                            
                                            spreads_found.append({
                                                'id': spread_id,
                                                'data': spread
                                            })
                                            
                                            # Check spread structure
                                            spread_keys = list(spread.keys())
                                            print(f"         🔑 Keys: {spread_keys[:10]}")
                        
                        # Also check for direct catalog structure
                        catalog_keys = [k for k in data.keys() if any(term in k.lower() for term in ['catalog', 'page', 'spread', 'brochure'])]
                        if catalog_keys:
                            print(f"\n📖 Direct catalog keys found: {catalog_keys}")
                            
                            for key in catalog_keys:
                                value = data[key]
                                print(f"   📋 {key}: {type(value)}")
                                if isinstance(value, list):
                                    print(f"      📊 Length: {len(value)}")
                
                except json.JSONDecodeError:
                    continue
        
        # Test accessing individual pages/spreads
        print(f"\n🧪 Testing Page/Spread Access:")
        
        if pages_found:
            test_page = pages_found[0]
            test_urls = [
                f"https://ereklamblad.se/Willys?publication={publication_id}&page={test_page['id']}",
                f"https://ereklamblad.se/Willys/{publication_id}/page/{test_page['id']}",
                f"https://ereklamblad.se/Willys?publication={publication_id}&pageNumber={test_page['number']}"
            ]
            
            for test_url in test_urls:
                print(f"   📡 Testing page access: {test_url}")
                try:
                    test_response = session.get(test_url, timeout=10)
                    print(f"      Status: {test_response.status_code}")
                    
                    if test_response.status_code == 200 and 'app-data' in test_response.text:
                        # Quick check for offers
                        offer_pattern = r'"(?:name|title)"\s*:\s*"([^"]{10,50})".*?"(?:price|amount)"'
                        offers_match = re.findall(offer_pattern, test_response.text, re.IGNORECASE | re.DOTALL)
                        
                        if offers_match:
                            print(f"      ✅ Found {len(offers_match)} potential offers!")
                            for j, offer_name in enumerate(offers_match[:3]):
                                print(f"         🛍️ {j+1}. {offer_name}")
                            return pages_found, spreads_found, "individual_pages"
                        else:
                            print(f"      ℹ️ Page accessible but no clear offers found")
                    
                except Exception as e:
                    print(f"      💥 Error: {e}")
        
        if spreads_found:
            test_spread = spreads_found[0]
            test_urls = [
                f"https://ereklamblad.se/Willys?publication={publication_id}&spread={test_spread['id']}",
                f"https://ereklamblad.se/Willys/{publication_id}/spread/{test_spread['id']}"
            ]
            
            for test_url in test_urls:
                print(f"   📡 Testing spread access: {test_url}")
                try:
                    test_response = session.get(test_url, timeout=10)
                    print(f"      Status: {test_response.status_code}")
                    
                    if test_response.status_code == 200:
                        print(f"      ✅ Spread accessible")
                
                except Exception as e:
                    print(f"      💥 Error: {e}")
        
        return pages_found, spreads_found, "catalog_structure"
    
    else:
        print(f"❌ Failed to load publication")
        return [], [], "error"

if __name__ == "__main__":
    pages, spreads, structure = analyze_willys_catalog()
    
    print(f"\n🎯 Willys Catalog Analysis Results:")
    print(f"   📄 Pages found: {len(pages)}")
    print(f"   📖 Spreads found: {len(spreads)}")
    print(f"   🏗️ Structure type: {structure}")
    
    if pages:
        print(f"\n📄 Page Structure:")
        for i, page in enumerate(pages[:5], 1):
            print(f"   {i}. Page {page['number']} (ID: {page['id']})")
    
    if spreads:
        print(f"\n📖 Spread Structure:")
        for i, spread in enumerate(spreads[:5], 1):
            print(f"   {i}. Spread ID: {spread['id']}")
    
    if structure == "individual_pages":
        print(f"✅ Successfully found Willys offers in individual pages!")
        print(f"   Can scrape offers from each page separately")
    elif pages or spreads:
        print(f"📖 Found catalog structure - may need to analyze page content")
    else:
        print(f"❓ Unable to determine clear structure")
