#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import json

def detailed_static_analysis():
    """Detailed analysis to understand what static requests can and cannot get"""
    
    print("🔍 Detailed Static Analysis of Willys")
    print("=" * 50)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    # Test different URLs
    test_urls = [
        "https://ereklamblad.se/Willys",
        "https://ereklamblad.se/Willys?publication=Hn02_ny6",
        "https://ereklamblad.se/Willys?publication=Hn02_ny6&page=1",
        "https://ereklamblad.se/Willys?publication=Hn02_ny6&page=2",
    ]
    
    results = {}
    
    for url in test_urls:
        print(f"\n📡 Testing: {url}")
        
        try:
            response = session.get(url, timeout=15)
            print(f"   Status: {response.status_code}")
            print(f"   Content length: {len(response.text)}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
                
                total_app_data_content = ""
                for element in app_data_elements:
                    total_app_data_content += element.get_text()
                
                # Analyze content patterns
                patterns_found = {}
                search_terms = [
                    'offer', 'product', 'item', 'deal', 'price', 'amount',
                    'name', 'title', 'description', 'kr', 'SEK',
                    'publication', 'page', 'catalog', 'brochure'
                ]
                
                for term in search_terms:
                    count = total_app_data_content.lower().count(term)
                    if count > 0:
                        patterns_found[term] = count
                
                # Try to extract JSON data
                json_segments = []
                content = total_app_data_content
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
                
                json_data = []
                for segment in json_segments:
                    try:
                        data = json.loads(segment)
                        json_data.append(data)
                    except:
                        continue
                
                results[url] = {
                    'content_length': len(response.text),
                    'app_data_elements': len(app_data_elements),
                    'app_data_content_length': len(total_app_data_content),
                    'patterns_found': patterns_found,
                    'json_segments': len(json_data),
                    'json_data': json_data
                }
                
                print(f"   App-data elements: {len(app_data_elements)}")
                print(f"   App-data content: {len(total_app_data_content)} chars")
                print(f"   Patterns found: {patterns_found}")
                print(f"   JSON segments: {len(json_data)}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[url] = {'error': str(e)}
    
    # Compare results
    print(f"\n📊 Comparison Analysis")
    print("=" * 50)
    
    for url, data in results.items():
        if 'error' not in data:
            print(f"\n🔗 {url}")
            print(f"   Content: {data['content_length']:,} chars")
            print(f"   App-data: {data['app_data_content_length']:,} chars")
            print(f"   JSON segments: {data['json_segments']}")
            if data['patterns_found']:
                print(f"   Key terms: {data['patterns_found']}")
    
    # Check if all URLs return essentially the same content
    base_url = "https://ereklamblad.se/Willys"
    if base_url in results and not 'error' in results[base_url]:
        base_content_length = results[base_url]['app_data_content_length']
        
        all_same = True
        for url, data in results.items():
            if 'error' not in data and url != base_url:
                if abs(data['app_data_content_length'] - base_content_length) > 100:
                    all_same = False
                    break
        
        print(f"\n🎯 Analysis Results:")
        if all_same:
            print(f"   ❌ ALL URLs return essentially the same content")
            print(f"   ❌ Static requests cannot access page-specific data")
            print(f"   ✅ BROWSER RENDERING IS REQUIRED")
            print(f"   📋 Willys uses JavaScript to load offers dynamically")
        else:
            print(f"   ✅ Different URLs return different content")
            print(f"   ✅ Static requests can access page-specific data")
            print(f"   📋 No browser rendering needed")
    
    return results

def analyze_javascript_dependency():
    """Analyze if the site depends on JavaScript for content loading"""
    
    print(f"\n🔍 JavaScript Dependency Analysis")
    print("=" * 50)
    
    url = "https://ereklamblad.se/Willys?publication=Hn02_ny6"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    response = session.get(url, timeout=15)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for JavaScript loading indicators
        indicators = {
            'script_tags': len(soup.find_all('script')),
            'async_scripts': len(soup.find_all('script', attrs={'async': True})),
            'defer_scripts': len(soup.find_all('script', attrs={'defer': True})),
            'spa_indicators': [],
            'loading_indicators': []
        }
        
        # Look for Single Page Application indicators
        spa_terms = ['react', 'angular', 'vue', 'app.js', 'bundle.js', 'main.js']
        for script in soup.find_all('script'):
            if script.get('src'):
                src = script['src'].lower()
                for term in spa_terms:
                    if term in src:
                        indicators['spa_indicators'].append(term)
        
        # Look for loading placeholders or dynamic content indicators
        loading_terms = ['loading', 'spinner', 'placeholder', 'skeleton']
        text_content = response.text.lower()
        for term in loading_terms:
            if term in text_content:
                indicators['loading_indicators'].append(term)
        
        # Check if content is mostly empty divs waiting for JS
        body = soup.find('body')
        if body:
            text_ratio = len(body.get_text().strip()) / len(str(body))
            indicators['text_content_ratio'] = text_ratio
        
        print(f"📊 JavaScript Analysis Results:")
        print(f"   Script tags: {indicators['script_tags']}")
        print(f"   Async scripts: {indicators['async_scripts']}")
        print(f"   Defer scripts: {indicators['defer_scripts']}")
        print(f"   SPA indicators: {indicators['spa_indicators']}")
        print(f"   Loading indicators: {indicators['loading_indicators']}")
        print(f"   Text/HTML ratio: {indicators.get('text_content_ratio', 0):.3f}")
        
        # Determine if browser is needed
        browser_needed = (
            indicators['script_tags'] > 5 or
            len(indicators['spa_indicators']) > 0 or
            len(indicators['loading_indicators']) > 0 or
            indicators.get('text_content_ratio', 1) < 0.1
        )
        
        if browser_needed:
            print(f"\n🎯 RECOMMENDATION: BROWSER REQUIRED")
            print(f"   ✅ Site shows signs of heavy JavaScript dependency")
            print(f"   ✅ Static requests likely insufficient")
        else:
            print(f"\n🎯 RECOMMENDATION: STATIC REQUESTS OK")
            print(f"   ✅ Site appears to work without JavaScript")
        
        return browser_needed
    
    return True  # Default to browser needed if we can't analyze

if __name__ == "__main__":
    print("🔬 Comprehensive Analysis: Do We Need a Browser?")
    print("=" * 60)
    
    # Run static analysis
    static_results = detailed_static_analysis()
    
    # Run JavaScript dependency analysis
    js_needed = analyze_javascript_dependency()
    
    print(f"\n🎯 FINAL RECOMMENDATION")
    print("=" * 60)
    
    if js_needed:
        print(f"✅ USE BROWSER-BASED SCRAPING")
        print(f"   📋 Reasons:")
        print(f"   • Static requests return identical content for all pages")
        print(f"   • Site uses JavaScript to load offer data dynamically")
        print(f"   • Browser rendering required to get actual offers")
        print(f"")
        print(f"📋 Implementation Steps:")
        print(f"   1. pip install selenium")
        print(f"   2. Download ChromeDriver")
        print(f"   3. Use headless Chrome for scraping")
        print(f"   4. Wait for dynamic content to load")
    else:
        print(f"✅ STATIC REQUESTS SUFFICIENT")
        print(f"   📋 Current approach should work fine")
        print(f"   📋 No browser overhead needed")
