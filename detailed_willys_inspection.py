#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
import re

def detailed_willys_inspection():
    """Detailed inspection of Willys publication data"""
    
    print("🔬 Detailed Willys Publication Inspection")
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
    print(f"📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
        
        for i, element in enumerate(app_data_elements):
            content = element.get_text().strip()
            print(f"\n📦 App-data element {i+1} ({len(content)} chars)")
            
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
            
            for j, segment in enumerate(json_segments):
                try:
                    data = json.loads(segment)
                    print(f"\n   ✅ JSON Segment {j+1}:")
                    
                    if isinstance(data, dict):
                        # Print all top-level keys and their types
                        print(f"      🔑 All keys ({len(data)} total):")
                        for key in sorted(data.keys()):
                            value = data[key]
                            value_type = type(value).__name__
                            
                            if isinstance(value, (list, dict, str)) and len(str(value)) > 100:
                                size_info = f"({len(value)} items)" if isinstance(value, list) else f"({len(str(value))} chars)"
                            else:
                                size_info = ""
                            
                            print(f"         {key}: {value_type} {size_info}")
                            
                            # Special handling for 'publication' key
                            if key == 'publication' and isinstance(value, dict):
                                print(f"         📚 Publication details:")
                                pub_keys = sorted(value.keys())
                                for pub_key in pub_keys:
                                    pub_value = value[pub_key]
                                    pub_type = type(pub_value).__name__
                                    
                                    if isinstance(pub_value, list):
                                        size_info = f"({len(pub_value)} items)"
                                    elif isinstance(pub_value, str) and len(pub_value) > 50:
                                        size_info = f"({len(pub_value)} chars)"
                                    else:
                                        size_info = ""
                                    
                                    print(f"            {pub_key}: {pub_type} {size_info}")
                                    
                                    # If it's a small list or dict, show the content
                                    if isinstance(pub_value, list) and len(pub_value) <= 5:
                                        print(f"               Content: {pub_value}")
                                    elif isinstance(pub_value, dict) and len(pub_value) <= 3:
                                        print(f"               Content: {pub_value}")
                                    elif isinstance(pub_value, str) and len(pub_value) <= 100:
                                        print(f"               Content: {pub_value}")
                        
                        # Look for any URLs or links in the data
                        json_str = json.dumps(data, indent=2)
                        
                        # Search for URLs
                        url_patterns = [
                            r'https?://[^\s"]+',
                            r'"/[^"\s]*"',  # Relative URLs
                        ]
                        
                        all_urls = []
                        for pattern in url_patterns:
                            urls = re.findall(pattern, json_str)
                            all_urls.extend(urls)
                        
                        if all_urls:
                            print(f"      🔗 URLs found ({len(all_urls)} total):")
                            unique_urls = list(set(all_urls))[:10]  # Show first 10 unique URLs
                            for url in unique_urls:
                                clean_url = url.strip('"')
                                print(f"         {clean_url}")
                        
                        # Look for any IDs that might be pages or offers
                        id_patterns = [
                            r'"id"\s*:\s*"([a-zA-Z0-9_-]{6,})"',
                            r'"pageId"\s*:\s*"([a-zA-Z0-9_-]{6,})"',
                            r'"offerId"\s*:\s*"([a-zA-Z0-9_-]{6,})"',
                            r'"publicId"\s*:\s*"([a-zA-Z0-9_-]{6,})"',
                        ]
                        
                        all_ids = []
                        for pattern in id_patterns:
                            ids = re.findall(pattern, json_str)
                            all_ids.extend([(id_val, pattern) for id_val in ids])
                        
                        if all_ids:
                            print(f"      🆔 IDs found ({len(all_ids)} total):")
                            for id_val, pattern_used in all_ids[:15]:  # Show first 15 IDs
                                pattern_name = pattern_used.split('"')[1]  # Extract the key name
                                print(f"         {pattern_name}: {id_val}")
                
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON Segment {j+1}: Parse error")
                    print(f"      Error: {str(e)}")
                    
                    # Show first few lines of problematic content
                    lines = segment.split('\n')[:5]
                    print(f"      Content preview:")
                    for line_num, line in enumerate(lines, 1):
                        preview = line[:100] + "..." if len(line) > 100 else line
                        print(f"         {line_num}: {preview}")
        
        # Also check if there are any other patterns in the raw HTML
        print(f"\n🔍 Raw HTML Analysis:")
        
        # Look for script tags or other data
        scripts = soup.find_all('script')
        print(f"   📜 Script tags found: {len(scripts)}")
        
        for i, script in enumerate(scripts[:5]):  # Check first 5 scripts
            if script.string:
                content = script.string.strip()
                if len(content) > 100:
                    print(f"      Script {i+1}: {len(content)} chars")
                    
                    # Look for ereklamblad-specific patterns
                    if 'ereklamblad' in content.lower():
                        print(f"         Contains ereklamblad references")
                    
                    # Look for offer or product patterns
                    offer_patterns = ['offer', 'product', 'item', 'deal', 'page']
                    found_patterns = [p for p in offer_patterns if p in content.lower()]
                    if found_patterns:
                        print(f"         Contains: {found_patterns}")

if __name__ == "__main__":
    detailed_willys_inspection()
