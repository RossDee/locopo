#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium not available - will only test static requests")
import json
import time

def compare_static_vs_dynamic():
    """Compare static requests vs browser-rendered content"""
    
    print("🔍 Static vs Dynamic Content Comparison")
    print("=" * 60)
    
    url = "https://ereklamblad.se/Willys"
    
    # === STATIC REQUESTS METHOD ===
    print("\n📡 Method 1: Static Requests")
    print("-" * 30)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    try:
        static_response = session.get(url, timeout=15)
        print(f"✅ Static request successful")
        print(f"   Status: {static_response.status_code}")
        print(f"   Content length: {len(static_response.text)}")
        
        static_soup = BeautifulSoup(static_response.text, 'html.parser')
        static_app_data = static_soup.find_all(id=lambda x: x and 'app-data' in x)
        print(f"   App-data elements: {len(static_app_data)}")
        
        # Count potential publications in static content
        static_pubs = 0
        static_content_size = 0
        for element in static_app_data:
            content = element.get_text()
            static_content_size += len(content)
            if 'publications' in content:
                static_pubs += content.count('publications')
        
        print(f"   Total app-data content: {static_content_size} chars")
        print(f"   'publications' mentions: {static_pubs}")
        
    except Exception as e:
        print(f"❌ Static request failed: {e}")
        static_response = None
    
    # === SELENIUM BROWSER METHOD ===
    print(f"\n🌐 Method 2: Selenium Browser (Chrome)")
    print("-" * 30)
    
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium not installed - skipping browser test")
        print("   Install with: pip install selenium")
        dynamic_html = None
        dynamic_app_data = []
        dynamic_content_size = 0
        dynamic_pubs = 0
    else:
        try:
            # Setup Chrome options for headless browsing
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            print("🚀 Starting Chrome browser...")
            driver = webdriver.Chrome(options=chrome_options)
            
            print(f"📡 Loading page: {url}")
            driver.get(url)
            
            # Wait for page to fully load
            print("⏳ Waiting for page to load...")
            time.sleep(5)  # Give time for JS to execute
            
            # Wait for app-data elements to be present
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[id*='app-data']"))
                )
                print("✅ App-data elements detected")
            except:
                print("⚠️ App-data elements not detected in 10s")
            
            # Get page source after JS execution
            dynamic_html = driver.page_source
            print(f"✅ Dynamic content captured")
            print(f"   Content length: {len(dynamic_html)}")
            
            dynamic_soup = BeautifulSoup(dynamic_html, 'html.parser')
            dynamic_app_data = dynamic_soup.find_all(id=lambda x: x and 'app-data' in x)
            print(f"   App-data elements: {len(dynamic_app_data)}")
            
            # Count potential publications in dynamic content
            dynamic_pubs = 0
            dynamic_content_size = 0
            for element in dynamic_app_data:
                content = element.get_text()
                dynamic_content_size += len(content)
                if 'publications' in content:
                    dynamic_pubs += content.count('publications')
            
            print(f"   Total app-data content: {dynamic_content_size} chars")
            print(f"   'publications' mentions: {dynamic_pubs}")
            
            # Check for any additional content that might be JS-loaded
            js_scripts = dynamic_soup.find_all('script')
            js_content_size = sum(len(script.get_text()) for script in js_scripts if script.get_text())
            print(f"   JavaScript content: {js_content_size} chars")
            
            driver.quit()
            
        except Exception as e:
            print(f"❌ Browser method failed: {e}")
            print("   Chrome WebDriver might not be installed")
            print("   Try: pip install selenium")
            print("   And install ChromeDriver from: https://chromedriver.chromium.org/")
            dynamic_html = None
            dynamic_app_data = []
            dynamic_content_size = 0
            dynamic_pubs = 0
    
    # === COMPARISON ANALYSIS ===
    print(f"\n📊 Comparison Analysis")
    print("=" * 60)
    
    if static_response and dynamic_html:
        print(f"📏 Content Length Comparison:")
        print(f"   Static:  {len(static_response.text):,} chars")
        print(f"   Dynamic: {len(dynamic_html):,} chars")
        diff_percent = ((len(dynamic_html) - len(static_response.text)) / len(static_response.text)) * 100
        print(f"   Difference: {diff_percent:+.1f}%")
        
        print(f"\n📦 App-data Comparison:")
        print(f"   Static app-data:  {len(static_app_data)} elements, {static_content_size:,} chars")
        print(f"   Dynamic app-data: {len(dynamic_app_data)} elements, {dynamic_content_size:,} chars")
        
        print(f"\n📚 Publications Comparison:")
        print(f"   Static mentions:  {static_pubs}")
        print(f"   Dynamic mentions: {dynamic_pubs}")
        
        # Determine if browser is needed
        significant_diff = abs(diff_percent) > 10 or dynamic_pubs > static_pubs or len(dynamic_app_data) > len(static_app_data)
        
        if significant_diff:
            print(f"\n🎯 Recommendation: USE BROWSER")
            print(f"   ✅ Significant differences detected")
            print(f"   ✅ Dynamic content appears more complete")
            return "browser_needed"
        else:
            print(f"\n🎯 Recommendation: STATIC REQUESTS OK")
            print(f"   ✅ No significant differences")
            print(f"   ✅ Static requests sufficient")
            return "static_sufficient"
    
    elif dynamic_html:
        print(f"🎯 Recommendation: USE BROWSER")
        print(f"   ✅ Browser method worked, static failed")
        return "browser_needed"
    
    elif static_response:
        print(f"🎯 Recommendation: STATIC REQUESTS")
        print(f"   ✅ Static method worked, browser failed")
        return "static_only"
    
    else:
        print(f"❌ Both methods failed")
        return "both_failed"

if __name__ == "__main__":
    recommendation = compare_static_vs_dynamic()
    
    print(f"\n🎯 Final Recommendation: {recommendation.upper()}")
    
    if recommendation == "browser_needed":
        print(f"📋 Next Steps:")
        print(f"   1. Install: pip install selenium")
        print(f"   2. Download ChromeDriver")
        print(f"   3. Implement browser-based scraper")
        print(f"   4. This will get more accurate data")
    
    elif recommendation == "static_sufficient":
        print(f"📋 Current approach is fine:")
        print(f"   ✅ Static requests work well")
        print(f"   ✅ No need for browser overhead")
    
    else:
        print(f"📋 Troubleshooting needed")
