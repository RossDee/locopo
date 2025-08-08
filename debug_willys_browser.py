#!/usr/bin/env python3

import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def debug_willys_browser_content():
    """Debug what content the browser actually loads"""
    
    print("🔍 Debugging Willys Browser Content")
    print("=" * 50)
    
    # Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Suppress Chrome logs
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        publication_id = "Hn02_ny6"
        url = f"https://ereklamblad.se/Willys?publication={publication_id}"
        
        print(f"📡 Loading: {url}")
        driver.get(url)
        
        # Wait longer for dynamic content
        print("⏳ Waiting for dynamic content...")
        time.sleep(10)
        
        # Try to wait for specific content to load
        try:
            # Wait for any element that might contain offers
            WebDriverWait(driver, 20).until(
                lambda driver: len(driver.page_source) > 50000
            )
            print("✅ Page content loaded")
        except:
            print("⚠️ Timeout waiting for content")
        
        # Get the full page source
        html_content = driver.page_source
        print(f"📊 Total content: {len(html_content):,} chars")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all app-data elements
        app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
        print(f"📦 App-data elements found: {len(app_data_elements)}")
        
        # Debug each app-data element
        for i, element in enumerate(app_data_elements):
            content = element.get_text().strip()
            print(f"\n📋 App-data element {i+1}:")
            print(f"   Length: {len(content):,} chars")
            print(f"   ID: {element.get('id', 'No ID')}")
            
            # Try to parse as JSON and show structure
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
            
            print(f"   JSON segments: {len(json_segments)}")
            
            for j, segment in enumerate(json_segments):
                try:
                    data = json.loads(segment)
                    print(f"   ✅ Segment {j+1} - Valid JSON")
                    
                    if isinstance(data, dict):
                        print(f"      Keys ({len(data)}): {list(data.keys())[:15]}")
                        
                        # Look for any arrays that might contain offers
                        array_keys = []
                        for key, value in data.items():
                            if isinstance(value, list) and len(value) > 0:
                                array_keys.append(f"{key}[{len(value)}]")
                        
                        if array_keys:
                            print(f"      Arrays found: {array_keys}")
                        
                        # Look for deeply nested content
                        def count_nested_objects(obj, depth=0):
                            if depth > 3:  # Limit recursion
                                return 0
                            
                            count = 0
                            if isinstance(obj, dict):
                                count += len(obj)
                                for value in obj.values():
                                    count += count_nested_objects(value, depth + 1)
                            elif isinstance(obj, list):
                                count += len(obj)
                                for item in obj:
                                    count += count_nested_objects(item, depth + 1)
                            return count
                        
                        nested_count = count_nested_objects(data)
                        print(f"      Nested objects: {nested_count}")
                        
                        # Look for specific offer-related keywords in the JSON
                        json_str = json.dumps(data, ensure_ascii=False)
                        keywords = ['offer', 'product', 'item', 'price', 'amount', 'kr', 'name', 'title']
                        keyword_counts = {}
                        
                        for keyword in keywords:
                            count = json_str.lower().count(keyword.lower())
                            if count > 0:
                                keyword_counts[keyword] = count
                        
                        if keyword_counts:
                            print(f"      Keywords found: {keyword_counts}")
                
                except json.JSONDecodeError as e:
                    print(f"   ❌ Segment {j+1} - JSON Error: {str(e)[:100]}...")
                    # Show a sample of the problematic content
                    sample = segment[:200].replace('\n', '\\n')
                    print(f"      Sample: {sample}...")
        
        # Also look for any script tags that might load data dynamically
        script_tags = soup.find_all('script')
        print(f"\n📜 Script tags found: {len(script_tags)}")
        
        data_scripts = 0
        for script in script_tags:
            if script.string:
                script_content = script.string.strip()
                if len(script_content) > 1000:  # Substantial scripts
                    data_scripts += 1
                    # Check if it contains offer-related content
                    if any(term in script_content.lower() for term in ['offer', 'product', 'price']):
                        print(f"   📊 Script contains offer-related content ({len(script_content)} chars)")
        
        print(f"   Data scripts: {data_scripts}")
        
        # Check for any elements that might be loaded dynamically
        print(f"\n🔍 Looking for dynamic elements...")
        
        # Wait a bit more and check if content changes
        time.sleep(5)
        updated_html = driver.page_source
        
        if len(updated_html) != len(html_content):
            print(f"📈 Content changed! New size: {len(updated_html):,} chars")
            print(f"   Difference: {len(updated_html) - len(html_content):+,} chars")
        else:
            print(f"📊 Content stable at {len(html_content):,} chars")
        
        # Try to interact with the page to trigger content loading
        print(f"\n🖱️ Trying to interact with page...")
        
        try:
            # Try clicking or scrolling to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Check for any buttons or links that might load offers
            buttons = driver.find_elements(By.TAG_NAME, "button")
            links = driver.find_elements(By.TAG_NAME, "a")
            
            print(f"   Found {len(buttons)} buttons, {len(links)} links")
            
            # Try to find elements with offer-related classes or IDs
            offer_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='offer'], [class*='product'], [id*='offer'], [id*='product']")
            print(f"   Offer-related elements: {len(offer_elements)}")
            
            if offer_elements:
                for i, elem in enumerate(offer_elements[:3]):
                    print(f"      Element {i+1}: {elem.tag_name} - {elem.get_attribute('class')} - {elem.get_attribute('id')}")
        
        except Exception as e:
            print(f"   ❌ Interaction error: {e}")
        
        return html_content
    
    finally:
        driver.quit()
        print("🧹 Browser closed")

if __name__ == "__main__":
    debug_willys_browser_content()
