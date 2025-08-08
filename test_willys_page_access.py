#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
import time

def test_page_access_methods():
    """Test different methods to access individual pages of Willys publication"""
    
    print("🧪 Testing Willys Page Access Methods")
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
    
    # Get page information from the publication first
    print(f"📡 Getting publication details...")
    pub_url = f"https://ereklamblad.se/Willys?publication={publication_id}"
    pub_response = session.get(pub_url, timeout=15)
    
    page_urls = []
    if pub_response.status_code == 200:
        soup = BeautifulSoup(pub_response.text, 'html.parser')
        app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
        
        # Look for page URLs or IDs in the publication data
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
                        pub_data = data['publication']
                        
                        print(f"📚 Publication Details:")
                        print(f"   Name: {pub_data.get('name', 'Unknown')}")
                        print(f"   Type: {pub_data.get('type', 'Unknown')}")
                        print(f"   Page Count: {pub_data.get('pageCount', 'Unknown')}")
                        
                        # Look for page-specific URLs or data
                        if 'images' in pub_data and isinstance(pub_data['images'], list):
                            print(f"   📄 Found {len(pub_data['images'])} page images")
                            
                            for i, img in enumerate(pub_data['images'][:5], 1):
                                if isinstance(img, dict):
                                    img_url = img.get('url', img.get('src', 'No URL'))
                                    print(f"      Page {i}: {img_url}")
                                    
                                    # Extract page identifier from image URL
                                    # Usually like: /Hn02_ny6/p-1.webp, /Hn02_ny6/p-2.webp
                                    if 'p-' in img_url:
                                        page_num = img_url.split('p-')[1].split('.')[0]
                                        page_urls.append(f"p-{page_num}")
                
                except json.JSONDecodeError:
                    continue
    
    print(f"\n🔍 Found potential page identifiers: {page_urls}")
    
    # Test various URL patterns for accessing pages
    test_patterns = [
        # Standard pagination patterns
        lambda p: f"https://ereklamblad.se/Willys?publication={publication_id}&page={p}",
        lambda p: f"https://ereklamblad.se/Willys?publication={publication_id}&pageNumber={p}",
        lambda p: f"https://ereklamblad.se/Willys?publication={publication_id}&p={p}",
        
        # Path-based patterns
        lambda p: f"https://ereklamblad.se/Willys/{publication_id}/page/{p}",
        lambda p: f"https://ereklamblad.se/Willys/{publication_id}/{p}",
        lambda p: f"https://ereklamblad.se/Willys/{publication_id}/p-{p}",
        
        # Fragment/hash patterns (though these won't work with requests)
        lambda p: f"https://ereklamblad.se/Willys?publication={publication_id}#page={p}",
        lambda p: f"https://ereklamblad.se/Willys?publication={publication_id}#p-{p}",
    ]
    
    # Test with page numbers and page identifiers
    test_values = ['1', '2', '3'] + page_urls[:3]
    
    successful_results = {}
    
    print(f"\n🧪 Testing {len(test_patterns)} URL patterns with {len(test_values)} page values:")
    
    base_content_length = None
    
    for pattern_num, pattern_func in enumerate(test_patterns, 1):
        print(f"\n📋 Pattern {pattern_num}: {pattern_func('X').replace('X', 'PAGE')}")
        
        for test_val in test_values:
            test_url = pattern_func(test_val)
            print(f"   Testing {test_val}: ", end="")
            
            try:
                response = session.get(test_url, timeout=10)
                content_length = len(response.text)
                
                if response.status_code == 200:
                    # Check if content is different from base
                    if base_content_length is None:
                        # Use first successful response as baseline
                        base_content_length = content_length
                        print(f"✅ {response.status_code} ({content_length:,} chars) [BASE]")
                    else:
                        diff = abs(content_length - base_content_length)
                        if diff > 1000:  # Significant difference
                            print(f"✅ {response.status_code} ({content_length:,} chars) [DIFFERENT +{diff:,}]")
                            
                            # This might be a real different page - analyze it
                            soup = BeautifulSoup(response.text, 'html.parser')
                            app_data = soup.find_all(id=lambda x: x and 'app-data' in x)
                            
                            if app_data:
                                successful_results[test_url] = {
                                    'content_length': content_length,
                                    'app_data_elements': len(app_data),
                                    'page_value': test_val,
                                    'pattern': pattern_num
                                }
                        elif diff > 100:
                            print(f"⚠️ {response.status_code} ({content_length:,} chars) [MINOR DIFF +{diff}]")
                        else:
                            print(f"➖ {response.status_code} ({content_length:,} chars) [SAME]")
                else:
                    print(f"❌ {response.status_code}")
                    
            except Exception as e:
                print(f"💥 Error: {str(e)[:50]}...")
            
            time.sleep(0.5)  # Be nice to server
    
    if successful_results:
        print(f"\n✅ Found {len(successful_results)} URLs with different content!")
        print(f"\n📊 Successful Page Access Methods:")
        
        for url, info in successful_results.items():
            print(f"   🎯 {url}")
            print(f"      Content: {info['content_length']:,} chars")
            print(f"      App-data: {info['app_data_elements']} elements")
            print(f"      Pattern: {info['pattern']}")
        
        # Test the best result for actual offers
        best_url = list(successful_results.keys())[0]
        print(f"\n🔍 Analyzing best result for offers: {best_url}")
        
        test_response = session.get(best_url, timeout=15)
        if test_response.status_code == 200:
            test_soup = BeautifulSoup(test_response.text, 'html.parser')
            test_app_data = test_soup.find_all(id=lambda x: x and 'app-data' in x)
            
            offers_found = 0
            for element in test_app_data:
                content = element.get_text()
                
                # Look for offer patterns
                offer_keywords = ['offer', 'product', 'price', 'amount', 'kr', 'SEK']
                for keyword in offer_keywords:
                    offers_found += content.lower().count(keyword)
            
            print(f"   🛍️ Potential offer keywords found: {offers_found}")
            
            if offers_found > 20:  # Significant number of offer-related terms
                print(f"   ✅ This looks like it contains offer data!")
                return successful_results, "offers_accessible"
            else:
                print(f"   ❌ Still no clear offer data found")
                return successful_results, "pages_different_no_offers"
    
    else:
        print(f"\n❌ No URLs returned significantly different content")
        print(f"📋 This suggests:")
        print(f"   • All page parameters are ignored by server")
        print(f"   • Content is loaded dynamically via JavaScript")
        print(f"   • Browser rendering is required")
        
        return {}, "browser_required"

if __name__ == "__main__":
    results, status = test_page_access_methods()
    
    print(f"\n🎯 Final Assessment: {status.upper()}")
    
    if status == "offers_accessible":
        print(f"✅ SUCCESS: Found working page access method!")
        print(f"   📋 Can scrape offers using static requests")
        print(f"   📋 No browser needed")
    
    elif status == "pages_different_no_offers":
        print(f"⚠️ PARTIAL: Pages accessible but no offers found")
        print(f"   📋 May still need browser for dynamic content")
    
    elif status == "browser_required":
        print(f"❌ BROWSER REQUIRED: Static requests insufficient")
        print(f"   📋 Content is loaded dynamically")
        print(f"   📋 Need to implement Selenium-based scraper")
    
    if results:
        print(f"\n📋 Working URLs found:")
        for url in list(results.keys())[:3]:
            print(f"   • {url}")
    
    print(f"\n💡 Next Steps:")
    if status == "browser_required":
        print(f"   1. Install Selenium: pip install selenium")
        print(f"   2. Download ChromeDriver")
        print(f"   3. Implement browser-based Willys scraper")
    else:
        print(f"   1. Integrate working URL patterns into scraper")
        print(f"   2. Test offer extraction from accessible pages")
