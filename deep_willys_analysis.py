#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
import re

def deep_analyze_willys_offers():
    """Deep analysis of Willys publication to find offers structure"""
    
    print("🔍 Deep Willys Offers Analysis")
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
    print(f"🔗 URL: {url}")
    
    response = session.get(url, timeout=15)
    print(f"📊 Status: {response.status_code}, Length: {len(response.text)}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find app-data elements
        app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
        print(f"🔍 Found {len(app_data_elements)} app-data elements")
        
        all_offers = []
        
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
                        print(f"   ✅ Segment {j+1}: Valid JSON ({len(str(data))} chars)")
                        
                        if isinstance(data, dict):
                            print(f"      🔑 Top keys: {list(data.keys())[:15]}")
                            
                            # Look for different possible keys that might contain offers
                            potential_offer_keys = []
                            for key in data.keys():
                                if any(term in key.lower() for term in ['offer', 'deal', 'product', 'item', 'article', 'catalog', 'page', 'spread']):
                                    potential_offer_keys.append(key)
                            
                            if potential_offer_keys:
                                print(f"      🎯 Potential offer keys: {potential_offer_keys}")
                                
                                for key in potential_offer_keys:
                                    value = data[key]
                                    print(f"         📋 {key}: {type(value)}")
                                    
                                    if isinstance(value, list):
                                        print(f"            📊 Array length: {len(value)}")
                                        if len(value) > 0:
                                            print(f"            🔍 First item type: {type(value[0])}")
                                            if isinstance(value[0], dict):
                                                print(f"            🔑 First item keys: {list(value[0].keys())[:10]}")
                                                
                                                # Check if this looks like offers
                                                first_item = value[0]
                                                if any(offer_key in first_item for offer_key in ['name', 'title', 'price', 'description', 'id']):
                                                    print(f"            ✅ Looks like offers!")
                                                    
                                                    # Extract sample offers
                                                    sample_count = min(3, len(value))
                                                    for k in range(sample_count):
                                                        offer = value[k]
                                                        offer_id = offer.get('id', offer.get('publicId', f'unknown_{k}'))
                                                        offer_name = offer.get('name', offer.get('title', 'Unknown Offer'))
                                                        offer_price = offer.get('price', offer.get('amount', 'No price'))
                                                        
                                                        print(f"               🛍️ Offer {k+1}: {offer_name}")
                                                        print(f"                  ID: {offer_id}")
                                                        print(f"                  Price: {offer_price}")
                                                        
                                                        all_offers.append({
                                                            'id': offer_id,
                                                            'name': offer_name,
                                                            'price': offer_price,
                                                            'source_key': key,
                                                            'data': offer
                                                        })
                                    
                                    elif isinstance(value, dict):
                                        print(f"            🔑 Object keys: {list(value.keys())[:10]}")
                            
                            # Also look for deeply nested structures
                            def search_nested_offers(obj, path=""):
                                nested_offers = []
                                if isinstance(obj, dict):
                                    for k, v in obj.items():
                                        new_path = f"{path}.{k}" if path else k
                                        if k.lower() in ['offers', 'products', 'items', 'articles'] and isinstance(v, list):
                                            print(f"      🎯 Found nested offers at: {new_path}")
                                            print(f"         📊 Contains {len(v)} items")
                                            if len(v) > 0 and isinstance(v[0], dict):
                                                print(f"         🔑 Item keys: {list(v[0].keys())[:10]}")
                                                nested_offers.extend(v)
                                        elif isinstance(v, (dict, list)) and len(new_path.split('.')) < 4:
                                            nested_offers.extend(search_nested_offers(v, new_path))
                                elif isinstance(obj, list):
                                    for i, item in enumerate(obj[:5]):  # Limit to first 5 items
                                        nested_offers.extend(search_nested_offers(item, f"{path}[{i}]"))
                                return nested_offers
                            
                            nested = search_nested_offers(data)
                            if nested:
                                print(f"      🔍 Found {len(nested)} nested items")
                                all_offers.extend([{'id': f'nested_{i}', 'name': f'Nested item {i}', 'data': item} for i, item in enumerate(nested[:5])])
                    
                    except json.JSONDecodeError as e:
                        print(f"   ❌ Segment {j+1}: JSON parsing failed - {str(e)[:100]}...")
                        
                        # Maybe it's catalog-style - look for page structure
                        if 'page' in segment.lower() or 'catalog' in segment.lower():
                            print(f"      🔍 Checking for catalog-style structure...")
                            
                            # Count potential IDs
                            id_pattern = r'"id"\s*:\s*"([a-zA-Z0-9_-]{8,})"'
                            ids_found = re.findall(id_pattern, segment)
                            
                            if ids_found:
                                print(f"      📋 Found {len(ids_found)} potential IDs")
                                for id_sample in ids_found[:5]:
                                    print(f"         🆔 {id_sample}")
        
        print(f"\n📊 Offers Analysis Summary:")
        print(f"   🛍️ Total offers found: {len(all_offers)}")
        
        if all_offers:
            print(f"\n📋 Sample Offers:")
            for i, offer in enumerate(all_offers[:10], 1):
                print(f"   {i}. {offer['name']} (ID: {offer['id']})")
                if 'price' in offer:
                    print(f"      💰 Price: {offer['price']}")
                if 'source_key' in offer:
                    print(f"      📂 Source: {offer['source_key']}")
            
            # Determine structure type
            print(f"\n🔍 Structure Analysis:")
            source_keys = [offer.get('source_key', 'unknown') for offer in all_offers]
            unique_sources = set(source_keys)
            print(f"   📂 Data sources: {list(unique_sources)}")
            
            if len(unique_sources) == 1 and 'unknown' not in unique_sources:
                structure_type = "individual_offers"
                print(f"   ✅ Structure type: Individual offers (like ICA Maxi)")
            else:
                structure_type = "catalog_style"
                print(f"   ✅ Structure type: Catalog style (like Coop)")
            
            return all_offers, structure_type
        
        else:
            print(f"❌ No clear offers found")
            print(f"   This might be a catalog-style publication")
            print(f"   Let's check for catalog pages...")
            
            # Look for catalog pages or spreads
            catalog_indicators = ['catalog', 'page', 'spread', 'brochure']
            found_catalog = False
            
            for element in app_data_elements:
                content = element.get_text().lower()
                for indicator in catalog_indicators:
                    if indicator in content:
                        count = content.count(indicator)
                        print(f"   📄 Found '{indicator}' mentioned {count} times")
                        found_catalog = True
            
            if found_catalog:
                return [], "catalog_style"
            else:
                return [], "unknown"
    
    else:
        print(f"❌ Failed to load Willys publication: {response.status_code}")
        return [], "error"

if __name__ == "__main__":
    offers, structure_type = deep_analyze_willys_offers()
    
    print(f"\n🎯 Final Analysis Results:")
    print(f"   🛍️ Offers found: {len(offers)}")
    print(f"   🏗️ Structure type: {structure_type}")
    
    if offers:
        print(f"✅ Successfully discovered Willys offers structure!")
        print(f"   Ready to integrate into universal scraper")
    elif structure_type == "catalog_style":
        print(f"📖 Willys appears to use catalog-style publications")
        print(f"   Similar to Coop - needs catalog page analysis")
    else:
        print(f"❓ Unable to determine Willys structure")
        print(f"   May need alternative approach")
