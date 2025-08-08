#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup

def debug_coop_structure():
    """Deep debug of Coop app-data structure"""
    
    print("🔬 Deep Coop Structure Analysis")
    print("=" * 50)
    
    # Setup session
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
            
            # Find all app-data elements
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
            print(f"\n🔍 Found {len(app_data_elements)} app-data elements")
            
            for i, element in enumerate(app_data_elements):
                print(f"\n📦 App-data Element {i+1}:")
                print(f"   ID: {element.get('id', 'No ID')}")
                
                content = element.get_text().strip()
                print(f"   Length: {len(content)} characters")
                
                if content:
                    try:
                        # Parse JSON
                        data = json.loads(content)
                        print(f"   ✅ Valid JSON")
                        
                        # Show structure
                        if isinstance(data, dict):
                            print(f"   🔑 Top-level keys ({len(data)}): {list(data.keys())[:10]}")
                            
                            # Look for common patterns
                            for key in ['offers', 'items', 'products', 'data', 'publication']:
                                if key in data:
                                    value = data[key]
                                    if isinstance(value, list):
                                        print(f"   📋 '{key}' is a list with {len(value)} items")
                                        if value and isinstance(value[0], dict):
                                            sample_keys = list(value[0].keys())[:5]
                                            print(f"      Sample item keys: {sample_keys}")
                                    elif isinstance(value, dict):
                                        print(f"   📋 '{key}' is a dict with keys: {list(value.keys())[:5]}")
                                    else:
                                        print(f"   📋 '{key}': {type(value)} = {str(value)[:50]}...")
                            
                            # Search for any ID-like values
                            def find_ids(obj, path="", max_depth=3):
                                if max_depth <= 0:
                                    return []
                                
                                ids = []
                                if isinstance(obj, dict):
                                    for key, value in obj.items():
                                        new_path = f"{path}.{key}" if path else key
                                        
                                        # Check if this looks like an ID
                                        if isinstance(value, str) and len(value) >= 10 and value.replace('-', '').replace('_', '').isalnum():
                                            ids.append((new_path, value))
                                        else:
                                            ids.extend(find_ids(value, new_path, max_depth-1))
                                elif isinstance(obj, list):
                                    for j, item in enumerate(obj[:3]):  # Check first 3 items
                                        new_path = f"{path}[{j}]" if path else f"[{j}]"
                                        ids.extend(find_ids(item, new_path, max_depth-1))
                                
                                return ids
                            
                            potential_ids = find_ids(data)
                            if potential_ids:
                                print(f"   🎯 Potential IDs found:")
                                for path, id_value in potential_ids[:10]:  # Show first 10
                                    print(f"      {path}: {id_value}")
                                if len(potential_ids) > 10:
                                    print(f"      ... and {len(potential_ids) - 10} more")
                        else:
                            print(f"   📊 Data type: {type(data)}")
                            
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON parsing failed: {e}")
                        # Show first part of raw content
                        preview = content[:200].replace('\n', '\\n').replace('\r', '\\r')
                        print(f"   📝 Raw content preview: {preview}...")
                        
                    except Exception as e:
                        print(f"   💥 Error: {e}")
            
            # Also check for any script tags with interesting content
            print(f"\n🔍 Checking script tags...")
            scripts = soup.find_all('script')
            relevant_scripts = 0
            
            for script in scripts:
                if script.string and len(script.string.strip()) > 100:
                    content = script.string.strip()
                    if any(term in content.lower() for term in ['coop', 'offer', 'publication', 'suVwNFKv']):
                        relevant_scripts += 1
                        print(f"   📜 Relevant script {relevant_scripts}: {len(content)} chars")
                        if 'suVwNFKv' in content:
                            print(f"      🎯 Contains publication ID!")
            
            print(f"   Found {relevant_scripts} potentially relevant scripts")
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_coop_structure()
