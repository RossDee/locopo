#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
import re

def analyze_willys_publications():
    """Extract publications from Willys top-level page"""
    
    print("🔍 Willys Publications Analysis")
    print("=" * 50)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    url = "https://ereklamblad.se/Willys"
    response = session.get(url, timeout=15)
    
    print(f"📊 Status: {response.status_code}, Length: {len(response.text)}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find app-data elements
        app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
        print(f"🔍 Found {len(app_data_elements)} app-data elements")
        
        publications = []
        
        for i, element in enumerate(app_data_elements):
            print(f"\n📦 Analyzing app-data element {i+1}...")
            content = element.get_text().strip()
            print(f"   Content length: {len(content)} chars")
            
            if content:
                # Extract JSON segments using brace matching
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
                
                print(f"   🔍 Found {len(json_segments)} JSON segments")
                
                for j, segment in enumerate(json_segments):
                    try:
                        data = json.loads(segment)
                        print(f"   ✅ Segment {j+1}: Valid JSON")
                        
                        if isinstance(data, dict):
                            print(f"      🔑 Top keys: {list(data.keys())[:10]}")
                            
                            # Look for publications array
                            if 'publications' in data:
                                pubs = data['publications']
                                if isinstance(pubs, list):
                                    print(f"      📚 Found 'publications' array with {len(pubs)} items")
                                    
                                    for k, pub in enumerate(pubs):
                                        if isinstance(pub, dict):
                                            pub_id = pub.get('publicId', pub.get('id', f'unknown_{k}'))
                                            pub_name = pub.get('name', 'Unknown Publication')
                                            valid_until = pub.get('validUntil', 'Unknown')
                                            
                                            print(f"         📋 Publication {k+1}: {pub_name}")
                                            print(f"            ID: {pub_id}")
                                            print(f"            Valid until: {valid_until}")
                                            
                                            publications.append({
                                                'id': pub_id,
                                                'name': pub_name,
                                                'valid_until': valid_until,
                                                'data': pub
                                            })
                            
                            # Also check for any other interesting keys
                            interesting_keys = []
                            for key in data.keys():
                                if any(term in key.lower() for term in ['pub', 'catalog', 'brochure', 'flyer']):
                                    interesting_keys.append(key)
                            
                            if interesting_keys:
                                print(f"      🎯 Other interesting keys: {interesting_keys}")
                    
                    except json.JSONDecodeError as e:
                        print(f"   ❌ Segment {j+1}: JSON parsing failed - {str(e)[:100]}...")
                        # Show a preview of the problematic content
                        preview = segment[:200].replace('\n', '\\n')
                        print(f"      📝 Content preview: {preview}...")
        
        print(f"\n📊 Publications Summary:")
        print(f"   📚 Total publications found: {len(publications)}")
        
        if publications:
            print(f"\n📋 Publications List:")
            for i, pub in enumerate(publications, 1):
                print(f"   {i}. {pub['name']} (ID: {pub['id']})")
                print(f"      Valid until: {pub['valid_until']}")
            
            # Test accessing first publication
            if publications:
                test_pub = publications[0]
                print(f"\n🧪 Testing Publication Access: {test_pub['name']}")
                
                test_urls = [
                    f"https://ereklamblad.se/Willys?publication={test_pub['id']}",
                    f"https://ereklamblad.se/Willys/{test_pub['id']}"
                ]
                
                for test_url in test_urls:
                    print(f"   📡 Testing: {test_url}")
                    try:
                        test_response = session.get(test_url, timeout=10)
                        print(f"      Status: {test_response.status_code}")
                        
                        if test_response.status_code == 200:
                            print(f"      ✅ Successfully accessed publication!")
                            
                            # Quick check for offers in this publication
                            if 'app-data' in test_response.text:
                                test_soup = BeautifulSoup(test_response.text, 'html.parser')
                                test_app_data = test_soup.find_all(id=lambda x: x and 'app-data' in x)
                                
                                offer_count = 0
                                for test_element in test_app_data:
                                    test_content = test_element.get_text()
                                    # Simple count of potential offer IDs
                                    offer_matches = re.findall(r'"id"\s*:\s*"([a-zA-Z0-9_-]{10,})"', test_content)
                                    offer_count += len(offer_matches)
                                
                                print(f"      🛍️ Estimated offers in publication: {offer_count}")
                                
                                if offer_count > 0:
                                    print(f"      ✅ This publication contains offers!")
                                    return publications, test_pub['id']
                            break
                        else:
                            print(f"      ❌ Failed: {test_response.status_code}")
                            
                    except Exception as e:
                        print(f"      💥 Error: {e}")
        
        return publications, None
    
    else:
        print(f"❌ Failed to load Willys page: {response.status_code}")
        return [], None

if __name__ == "__main__":
    publications, test_pub_id = analyze_willys_publications()
    
    print(f"\n🎯 Final Results:")
    print(f"   📚 Publications found: {len(publications)}")
    
    if publications:
        print(f"✅ Successfully discovered Willys publications!")
        print(f"   Can extract offers from individual publications")
        
        if test_pub_id:
            print(f"   🧪 Tested publication access: SUCCESS")
            print(f"   📋 Ready to integrate Willys into scraper system")
        else:
            print(f"   🤔 Publications found but access testing failed")
    else:
        print(f"❌ No publications found")
        print(f"   Willys may use a different structure than expected")
