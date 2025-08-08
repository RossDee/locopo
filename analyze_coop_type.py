#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
import re

def analyze_coop_publication():
    """Analyze if Coop uses catalog-style vs individual offers"""
    
    print("📖 Coop Publication Type Analysis")
    print("=" * 50)
    
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
        soup = BeautifulSoup(response.text, 'html.parser')
        
        app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
        
        for element in app_data_elements:
            content = element.get_text().strip()
            
            # Extract JSON segments
            brace_level = 0
            start_pos = 0
            json_segments = []
            
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
            
            print(f"📊 Processing {len(json_segments)} JSON segments...")
            
            for i, segment in enumerate(json_segments):
                try:
                    data = json.loads(segment)
                    print(f"\n📦 Segment {i+1} Analysis:")
                    
                    if isinstance(data, dict):
                        print(f"   🔑 Keys: {list(data.keys())}")
                        
                        # Look for publication structure
                        if 'publication' in data:
                            pub_data = data['publication']
                            print(f"   📖 Publication data found!")
                            
                            if isinstance(pub_data, dict):
                                pub_keys = list(pub_data.keys())
                                print(f"      🔑 Publication keys: {pub_keys}")
                                
                                # Look for pages, offers, or catalog structure
                                for key in ['pages', 'offers', 'items', 'products', 'content']:
                                    if key in pub_data:
                                        value = pub_data[key]
                                        if isinstance(value, list):
                                            print(f"      📋 '{key}': list with {len(value)} items")
                                            if value and isinstance(value[0], dict):
                                                sample_item = value[0]
                                                print(f"         Sample keys: {list(sample_item.keys())[:10]}")
                                                
                                                # Check if items have product info
                                                product_fields = ['name', 'price', 'title', 'description', 'image']
                                                found_fields = [f for f in product_fields if f in sample_item]
                                                if found_fields:
                                                    print(f"         🛍️ Product fields found: {found_fields}")
                                                    
                                                    # Show sample product
                                                    print(f"         📦 Sample item:")
                                                    for field in found_fields[:3]:
                                                        value = sample_item[field]
                                                        if isinstance(value, str) and len(value) > 50:
                                                            value = value[:50] + "..."
                                                        print(f"            {field}: {value}")
                                        
                                        elif isinstance(value, dict):
                                            print(f"      📋 '{key}': dict with keys {list(value.keys())[:5]}")
                        
                        # Look for other interesting structures
                        catalog_indicators = ['pages', 'catalog', 'brochure', 'flyer']
                        offer_indicators = ['offers', 'deals', 'promotions', 'items']
                        
                        found_catalog = [k for k in data.keys() if any(ind in k.lower() for ind in catalog_indicators)]
                        found_offers = [k for k in data.keys() if any(ind in k.lower() for ind in offer_indicators)]
                        
                        if found_catalog:
                            print(f"   📖 Catalog indicators: {found_catalog}")
                        if found_offers:
                            print(f"   🛍️ Offer indicators: {found_offers}")
                        
                        # Check for any ID-like values that could be product/page IDs
                        def find_all_ids(obj, path="", max_depth=2):
                            ids = []
                            if max_depth <= 0:
                                return ids
                                
                            if isinstance(obj, dict):
                                for key, value in obj.items():
                                    new_path = f"{path}.{key}" if path else key
                                    
                                    if isinstance(value, str) and len(value) >= 8:
                                        # Could be an ID
                                        if re.match(r'^[a-zA-Z0-9_-]+$', value):
                                            ids.append((new_path, value))
                                    
                                    ids.extend(find_all_ids(value, new_path, max_depth-1))
                                    
                            elif isinstance(obj, list) and obj:
                                # Just check first few items
                                for j, item in enumerate(obj[:3]):
                                    new_path = f"{path}[{j}]" if path else f"[{j}]"
                                    ids.extend(find_all_ids(item, new_path, max_depth-1))
                            
                            return ids
                        
                        all_ids = find_all_ids(data)
                        
                        if all_ids:
                            print(f"   🆔 Found {len(all_ids)} ID-like values:")
                            # Group by type
                            id_types = {}
                            for path, id_val in all_ids[:20]:  # Show first 20
                                key = path.split('.')[-1] if '.' in path else path
                                if key not in id_types:
                                    id_types[key] = []
                                id_types[key].append(id_val)
                            
                            for key, ids in id_types.items():
                                print(f"      {key}: {ids[:3]}{'...' if len(ids) > 3 else ''} ({len(ids)} total)")
                
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"   💥 Error analyzing segment: {e}")
        
        print(f"\n🔍 Conclusion:")
        print(f"   The Coop publication appears to be catalog-style rather than individual offers.")
        print(f"   This means we need a different approach - extract product data from catalog pages.")
        
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_coop_publication()
