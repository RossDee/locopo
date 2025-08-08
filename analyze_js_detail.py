#!/usr/bin/env python3

import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def analyze_javascript_content():
    """Analyze the actual JavaScript content to understand data structure"""
    
    print("🔍 Analyzing JavaScript Content Detail")
    print("=" * 50)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        publication_id = "Hn02_ny6"
        url = f"https://ereklamblad.se/Willys?publication={publication_id}"
        
        print(f"📡 Loading: {url}")
        driver.get(url)
        time.sleep(10)
        
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        script_tags = soup.find_all('script')
        print(f"📜 Found {len(script_tags)} script tags")
        
        for i, script in enumerate(script_tags):
            if script.string:
                script_content = script.string.strip()
                
                if len(script_content) > 1500:  # Focus on larger scripts
                    offer_keywords = ['offer', 'product', 'item', 'price', 'amount']
                    keyword_count = sum(script_content.lower().count(kw) for kw in offer_keywords)
                    
                    if keyword_count > 5:
                        print(f"\n📋 Script {i+1} ({len(script_content):,} chars, {keyword_count} keywords)")
                        
                        # Show first few lines to understand structure
                        lines = script_content.split('\n')[:15]
                        print(f"   📝 First 15 lines:")
                        for j, line in enumerate(lines, 1):
                            preview = line.strip()[:100]
                            if preview:
                                print(f"      {j:2d}: {preview}")
                        
                        # Look for specific patterns
                        patterns_to_check = [
                            ('JSON objects', r'\{[^{}]*"[^"]*"[^{}]*\}'),
                            ('Arrays', r'\[[^\[\]]*\]'),
                            ('Function calls', r'\w+\([^)]*\)'),
                            ('Variable assignments', r'(?:var|const|let)\s+\w+\s*='),
                            ('Object properties', r'"\w+":\s*"[^"]*"'),
                        ]
                        
                        for pattern_name, pattern in patterns_to_check:
                            import re
                            matches = re.findall(pattern, script_content[:2000])  # First 2000 chars only
                            if matches:
                                print(f"   🎯 {pattern_name}: {len(matches)} matches")
                                # Show first few matches
                                for match in matches[:3]:
                                    preview = str(match)[:60].replace('\n', '\\n')
                                    print(f"      • {preview}")
                        
                        # Check for ereklamblad-specific patterns
                        ereklamblad_terms = ['ereklamblad', 'tjek', 'catalog', 'brochure', 'flyer']
                        found_terms = [term for term in ereklamblad_terms if term.lower() in script_content.lower()]
                        if found_terms:
                            print(f"   📚 eReklamblad terms: {found_terms}")
                        
                        # Look for API calls or data loading
                        api_patterns = [
                            r'fetch\s*\([^)]+\)',
                            r'XMLHttpRequest',
                            r'\.get\s*\([^)]+\)',
                            r'\.post\s*\([^)]+\)',
                            r'ajax',
                        ]
                        
                        api_found = []
                        for api_pattern in api_patterns:
                            if re.search(api_pattern, script_content, re.IGNORECASE):
                                api_found.append(api_pattern.strip('\\').replace('\\s*', ' ').replace('[^)]+', '(...)'))
                        
                        if api_found:
                            print(f"   📡 API calls found: {api_found}")
                        
                        # Try to find the actual data structure
                        # Look for large data blocks
                        data_blocks = re.findall(r'(\{[^{}]{100,}(?:\{[^{}]*\}[^{}]*)*\})', script_content)
                        if data_blocks:
                            print(f"   📊 Large data blocks: {len(data_blocks)}")
                            
                            for k, block in enumerate(data_blocks[:2]):  # Check first 2 blocks
                                try:
                                    # Try to parse as JSON
                                    data = json.loads(block)
                                    print(f"      Block {k+1}: Valid JSON with {len(data)} keys")
                                    if isinstance(data, dict):
                                        print(f"         Keys: {list(data.keys())[:10]}")
                                except json.JSONDecodeError:
                                    print(f"      Block {k+1}: Not valid JSON")
                                    # Show a sample anyway
                                    sample = block[:200].replace('\n', ' ')
                                    print(f"         Sample: {sample}...")
        
        # Also check for potential AJAX endpoints by looking at network activity
        print(f"\n🌐 Checking for dynamic content loading...")
        
        # Execute some JavaScript to see if there are global variables with offers
        try:
            # Try to access common global variables
            global_checks = [
                "typeof window.offers !== 'undefined' ? window.offers.length : 'undefined'",
                "typeof window.products !== 'undefined' ? window.products.length : 'undefined'",
                "typeof window.catalog !== 'undefined' ? Object.keys(window.catalog).length : 'undefined'",
                "typeof window.appData !== 'undefined' ? Object.keys(window.appData).length : 'undefined'",
                "document.querySelectorAll('[data-offer]').length",
                "document.querySelectorAll('[data-product]').length",
            ]
            
            for check in global_checks:
                try:
                    result = driver.execute_script(f"return {check}")
                    if result != 'undefined' and result > 0:
                        print(f"   ✅ {check} = {result}")
                except:
                    continue
        
        except Exception as e:
            print(f"   ❌ JavaScript execution error: {e}")
        
    finally:
        driver.quit()
        print("🧹 Browser closed")

if __name__ == "__main__":
    analyze_javascript_content()
