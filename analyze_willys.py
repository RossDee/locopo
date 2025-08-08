#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
import re

def analyze_willys_structure():
    """Analyze Willys eReklamblad structure from top level"""
    
    print("🏪 Willys eReklamblad Structure Analysis")
    print("=" * 60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    base_url = "https://ereklamblad.se/Willys"
    
    try:
        print(f"📡 Loading: {base_url}")
        response = session.get(base_url, timeout=15)
        
        print(f"📊 Status: {response.status_code}")
        print(f"📄 Content Length: {len(response.text)} chars")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check page title
            title = soup.find('title')
            if title:
                print(f"📄 Page Title: {title.get_text().strip()}")
            
            print("\n🔍 Analyzing app-data for publications...")
            
            # Find app-data elements
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
            print(f"   Found {len(app_data_elements)} app-data elements")
            
            publications = []
            offer_ids = set()
            
            for i, element in enumerate(app_data_elements):
                print(f"\n📦 Processing app-data element {i+1}...")
                content = element.get_text().strip()
                print(f"   Content length: {len(content)} chars")
                
                if content:
                    # Extract JSON segments
                    json_segments = extract_json_segments(content)
                    print(f"   🔍 Found {len(json_segments)} JSON segments")
                    
                    for j, segment in enumerate(json_segments):
                        try:
                            data = json.loads(segment)
                            print(f"   ✅ Segment {j+1}: Valid JSON")
                            
                            if isinstance(data, dict):
                                # Look for publication information
                                if 'publications' in data:
                                    pubs = data['publications']
                                    if isinstance(pubs, list):
                                        publications.extend(pubs)
                                        print(f"      📚 Found {len(pubs)} publications in this segment")
                                        
                                        for pub in pubs[:3]:  # Show first 3
                                            if isinstance(pub, dict):
                                                pub_id = pub.get('publicId') or pub.get('id') or pub.get('publication_id')
                                                pub_name = pub.get('name') or pub.get('title')
                                                print(f"         📋 Publication: {pub_name} (ID: {pub_id})")
                                
                                # Look for offers or items
                                for key in ['offers', 'items', 'products', 'deals']:
                                    if key in data:
                                        items = data[key]
                                        if isinstance(items, list):
                                            print(f"      🛍️ Found {len(items)} {key}")
                                            
                                            # Extract IDs from items
                                            for item in items:
                                                if isinstance(item, dict):
                                                    item_id = item.get('id') or item.get('offerId')
                                                    if item_id and isinstance(item_id, str) and len(item_id) >= 8:
                                                        offer_ids.add(item_id)
                                
                                # Recursively search for publication IDs and offer IDs
                                found_pubs, found_offers = search_for_ids(data)
                                publications.extend(found_pubs)
                                offer_ids.update(found_offers)
                                
                                # Show some key information
                                interesting_keys = [k for k in data.keys() 
                                                  if any(term in k.lower() 
                                                       for term in ['publication', 'offer', 'item', 'product', 'catalog'])]
                                if interesting_keys:
                                    print(f"      🔑 Interesting keys: {interesting_keys[:5]}")
                        
                        except json.JSONDecodeError as e:
                            print(f"   ❌ Segment {j+1}: JSON error - {e}")
                            
                            # Try regex extraction on malformed JSON
                            patterns = [
                                r'"publicId"\s*:\s*"([a-zA-Z0-9_-]+)"',
                                r'"publication_id"\s*:\s*"([a-zA-Z0-9_-]+)"',
                                r'"id"\s*:\s*"([a-zA-Z0-9_-]{8,})"',
                            ]
                            
                            for pattern in patterns:
                                matches = re.findall(pattern, segment)
                                if matches:
                                    print(f"      🎯 Regex found {len(matches)} IDs: {matches[:3]}...")
                                    offer_ids.update(matches)
            
            print(f"\n📊 Analysis Summary:")
            print(f"   📚 Publications found: {len(set(p.get('publicId', p.get('id', '')) for p in publications if isinstance(p, dict)))}")
            print(f"   🛍️ Potential offer IDs: {len(offer_ids)}")
            
            # Display unique publications
            unique_publications = {}
            for pub in publications:
                if isinstance(pub, dict):
                    pub_id = pub.get('publicId') or pub.get('id')
                    if pub_id and pub_id not in unique_publications:
                        unique_publications[pub_id] = pub
            
            if unique_publications:
                print(f"\n📚 Unique Publications:")
                for pub_id, pub_data in unique_publications.items():
                    name = pub_data.get('name', 'Unknown')
                    valid_until = pub_data.get('validUntil', 'Unknown')
                    print(f"   📋 {name}")
                    print(f"      ID: {pub_id}")
                    print(f"      Valid until: {valid_until}")
                    print(f"      Keys: {list(pub_data.keys())[:8]}")
                    print()
            
            if offer_ids:
                print(f"\n🛍️ Sample Offer IDs:")
                for i, offer_id in enumerate(sorted(list(offer_ids))[:10]):
                    print(f"   {i+1:2d}. {offer_id}")
                if len(offer_ids) > 10:
                    print(f"   ... and {len(offer_ids) - 10} more")
            
            # Test accessing a publication if we found any
            if unique_publications:
                test_pub_id = list(unique_publications.keys())[0]
                test_pub_name = unique_publications[test_pub_id].get('name', 'Unknown')
                
                print(f"\n🧪 Testing Publication Access: {test_pub_name} ({test_pub_id})")
                
                # Try different URL patterns
                test_urls = [
                    f"https://ereklamblad.se/Willys?publication={test_pub_id}",
                    f"https://ereklamblad.se/Willys/{test_pub_id}",
                ]
                
                for test_url in test_urls:
                    try:
                        print(f"   📡 Testing: {test_url}")
                        test_response = session.get(test_url, timeout=10)
                        print(f"      Status: {test_response.status_code}")
                        
                        if test_response.status_code == 200:
                            test_soup = BeautifulSoup(test_response.text, 'html.parser')
                            test_title = test_soup.find('title')
                            if test_title:
                                print(f"      Title: {test_title.get_text().strip()}")
                            
                            # Check for offer content
                            if 'willys' in test_response.text.lower():
                                print(f"      ✅ Contains Willys branding")
                            
                            # Look for offers in this publication
                            test_app_data = test_soup.find_all(id=lambda x: x and 'app-data' in x)
                            pub_offer_count = 0
                            for test_element in test_app_data:
                                test_content = test_element.get_text().strip()
                                test_segments = extract_json_segments(test_content)
                                for test_segment in test_segments:
                                    try:
                                        test_data = json.loads(test_segment)
                                        _, test_offers = search_for_ids(test_data)
                                        pub_offer_count += len(test_offers)
                                    except:
                                        pass
                            
                            print(f"      🛍️ Offers found in publication: {pub_offer_count}")
                            break
                            
                    except Exception as e:
                        print(f"      ❌ Error: {e}")
            
            return unique_publications, list(offer_ids)
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return {}, []

def extract_json_segments(content):
    """Extract valid JSON segments from content"""
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
    
    return json_segments

def search_for_ids(obj, path="", max_depth=3):
    """Recursively search for publication and offer IDs"""
    publications = []
    offer_ids = set()
    
    if max_depth <= 0:
        return publications, offer_ids
    
    if isinstance(obj, dict):
        # Check if this looks like a publication object
        if 'publicId' in obj or ('id' in obj and 'name' in obj and any(k in obj for k in ['validUntil', 'validFrom'])):
            publications.append(obj)
        
        # Look for offer-like IDs
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            
            if key.lower() in ['id', 'offerid', 'offer_id'] and isinstance(value, str) and len(value) >= 8:
                offer_ids.add(value)
            else:
                sub_pubs, sub_offers = search_for_ids(value, new_path, max_depth - 1)
                publications.extend(sub_pubs)
                offer_ids.update(sub_offers)
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{path}[{i}]" if path else f"[{i}]"
            sub_pubs, sub_offers = search_for_ids(item, new_path, max_depth - 1)
            publications.extend(sub_pubs)
            offer_ids.update(sub_offers)
    
    return publications, offer_ids

if __name__ == "__main__":
    publications, offers = analyze_willys_structure()
    
    print(f"\n🎯 Final Results:")
    print(f"   📚 Publications discovered: {len(publications)}")
    print(f"   🛍️ Potential offers: {len(offers)}")
    
    if publications:
        print(f"✅ Successfully identified Willys publications!")
        print(f"   Can proceed to extract offers from individual publications")
    else:
        print(f"🤔 No publications found in top-level page")
        print(f"   May need different approach or Willys uses different structure")
