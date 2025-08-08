#!/usr/bin/env python3

import requests
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

class WillysBrowserScraper:
    """Browser-based scraper for Willys eReklamblad"""
    
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8'
        })
    
    def _setup_driver(self):
        """Initialize Chrome WebDriver with optimal settings"""
        if self.driver:
            return
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # Performance and stability options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Speed up loading
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Suppress logging
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        print("🚀 Chrome browser initialized")
    
    def _cleanup_driver(self):
        """Clean up Chrome WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("🧹 Chrome browser closed")
    
    def discover_publications(self, retailer_url="https://ereklamblad.se/Willys"):
        """Discover available publications using static requests first"""
        print(f"📡 Discovering Willys publications...")
        
        try:
            response = self.session.get(retailer_url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Failed to load {retailer_url}: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
            
            publications = []
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
                        if isinstance(data, dict) and 'publications' in data:
                            pubs = data['publications']
                            if isinstance(pubs, list):
                                for pub in pubs:
                                    if isinstance(pub, dict):
                                        publications.append({
                                            'id': pub.get('publicId', pub.get('id')),
                                            'name': pub.get('name', 'Unknown Publication'),
                                            'valid_until': pub.get('validUntil'),
                                            'data': pub
                                        })
                    except json.JSONDecodeError:
                        continue
            
            print(f"📚 Found {len(publications)} publications")
            return publications
        
        except Exception as e:
            print(f"❌ Error discovering publications: {e}")
            return []
    
    def get_publication_details(self, publication_id):
        """Get detailed information about a publication using browser"""
        self._setup_driver()
        
        url = f"https://ereklamblad.se/Willys?publication={publication_id}"
        print(f"📡 Loading publication {publication_id} with browser...")
        
        try:
            self.driver.get(url)
            
            # Wait for dynamic content to load
            print("⏳ Waiting for content to load...")
            time.sleep(8)  # Give more time for JS to execute
            
            # Wait for app-data elements
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[id*='app-data']"))
                )
            except:
                print("⚠️ App-data elements not detected in 15s")
            
            # Get page source after JS execution
            html_content = self.driver.page_source
            print(f"✅ Captured {len(html_content):,} chars of dynamic content")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
            
            publication_data = None
            all_offers = []
            
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
                
                print(f"📦 Processing {len(json_segments)} JSON segments...")
                
                for i, segment in enumerate(json_segments):
                    try:
                        data = json.loads(segment)
                        
                        if isinstance(data, dict):
                            # Look for publication details
                            if 'publication' in data:
                                publication_data = data['publication']
                                print(f"📚 Publication: {publication_data.get('name', 'Unknown')}")
                                print(f"📄 Type: {publication_data.get('type', 'Unknown')}")
                                print(f"📊 Page count: {publication_data.get('pageCount', 'Unknown')}")
                            
                            # Look for offers in various locations
                            offers_found = self._extract_offers_from_data(data, f"segment_{i}")
                            if offers_found:
                                all_offers.extend(offers_found)
                                print(f"🛍️ Found {len(offers_found)} offers in segment {i+1}")
                    
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON parse error in segment {i+1}: {str(e)[:100]}...")
                        continue
            
            print(f"📊 Total offers found: {len(all_offers)}")
            
            return {
                'publication_data': publication_data,
                'offers': all_offers,
                'total_content_size': len(html_content)
            }
        
        except Exception as e:
            print(f"❌ Error loading publication: {e}")
            return None
    
    def _extract_offers_from_data(self, data, source="unknown"):
        """Extract offers from JSON data structure"""
        offers = []
        
        def search_for_offers(obj, path=""):
            if isinstance(obj, dict):
                # Direct offers array
                if 'offers' in obj and isinstance(obj['offers'], list):
                    for i, offer in enumerate(obj['offers']):
                        if isinstance(offer, dict):
                            offers.append(self._normalize_offer(offer, f"{source}.offers[{i}]"))
                
                # Products array
                elif 'products' in obj and isinstance(obj['products'], list):
                    for i, product in enumerate(obj['products']):
                        if isinstance(product, dict):
                            offers.append(self._normalize_offer(product, f"{source}.products[{i}]"))
                
                # Items array
                elif 'items' in obj and isinstance(obj['items'], list):
                    for i, item in enumerate(obj['items']):
                        if isinstance(item, dict):
                            offers.append(self._normalize_offer(item, f"{source}.items[{i}]"))
                
                # Catalog content
                elif 'catalog' in obj and isinstance(obj['catalog'], dict):
                    search_for_offers(obj['catalog'], f"{path}.catalog")
                
                # Pages content
                elif 'pages' in obj and isinstance(obj['pages'], list):
                    for i, page in enumerate(obj['pages']):
                        search_for_offers(page, f"{path}.pages[{i}]")
                
                # Search recursively in all dict values
                else:
                    for key, value in obj.items():
                        if isinstance(value, (dict, list)) and len(path.split('.')) < 4:  # Limit recursion depth
                            search_for_offers(value, f"{path}.{key}" if path else key)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, dict):
                        # Check if this list item looks like an offer
                        if any(key in item for key in ['name', 'title', 'price', 'amount']):
                            offers.append(self._normalize_offer(item, f"{source}[{i}]"))
                        else:
                            search_for_offers(item, f"{path}[{i}]")
        
        search_for_offers(data)
        return offers
    
    def _normalize_offer(self, offer_data, source):
        """Normalize offer data to standard format"""
        return {
            'id': offer_data.get('id', offer_data.get('offerId', offer_data.get('productId', 'unknown'))),
            'name': offer_data.get('name', offer_data.get('title', offer_data.get('productName', 'Unknown Product'))),
            'price': self._extract_price(offer_data),
            'description': offer_data.get('description', offer_data.get('subtitle', '')),
            'image_url': self._extract_image_url(offer_data),
            'valid_from': offer_data.get('validFrom', offer_data.get('startDate')),
            'valid_until': offer_data.get('validUntil', offer_data.get('endDate')),
            'source': source,
            'raw_data': offer_data
        }
    
    def _extract_price(self, data):
        """Extract price from various possible formats"""
        # Try different price keys
        price_keys = ['price', 'amount', 'cost', 'value']
        for key in price_keys:
            if key in data:
                price_value = data[key]
                if isinstance(price_value, (int, float)):
                    return float(price_value)
                elif isinstance(price_value, str):
                    # Extract numbers from string
                    numbers = re.findall(r'\d+[\.,]?\d*', price_value)
                    if numbers:
                        return float(numbers[0].replace(',', '.'))
        
        # Try nested price objects
        if 'pricing' in data and isinstance(data['pricing'], dict):
            return self._extract_price(data['pricing'])
        
        return None
    
    def _extract_image_url(self, data):
        """Extract image URL from various possible formats"""
        image_keys = ['image', 'imageUrl', 'picture', 'photo', 'thumbnail']
        for key in image_keys:
            if key in data:
                img_value = data[key]
                if isinstance(img_value, str) and img_value.startswith('http'):
                    return img_value
                elif isinstance(img_value, dict) and 'url' in img_value:
                    return img_value['url']
        
        return None
    
    def scrape_willys_offers(self):
        """Complete Willys scraping workflow"""
        print("🎯 Starting Willys Browser Scraping")
        print("=" * 50)
        
        try:
            # Step 1: Discover publications
            publications = self.discover_publications()
            if not publications:
                print("❌ No publications found")
                return {}
            
            # Step 2: Process each publication
            all_results = {}
            
            for pub in publications:
                pub_id = pub['id']
                pub_name = pub['name']
                print(f"\n📚 Processing publication: {pub_name} ({pub_id})")
                
                # Get detailed data with browser
                result = self.get_publication_details(pub_id)
                
                if result and result['offers']:
                    all_results[pub_id] = {
                        'publication_name': pub_name,
                        'publication_data': result['publication_data'],
                        'offers_count': len(result['offers']),
                        'offers': result['offers'],
                        'content_size': result['total_content_size']
                    }
                    
                    print(f"✅ Successfully extracted {len(result['offers'])} offers")
                    
                    # Show sample offers
                    for i, offer in enumerate(result['offers'][:3], 1):
                        print(f"   {i}. {offer['name']} - {offer['price']} kr")
                else:
                    print(f"❌ No offers found in publication {pub_name}")
                
                # Be nice to the server
                time.sleep(2)
            
            return all_results
        
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return {}
        
        finally:
            self._cleanup_driver()

def main():
    """Test the Willys browser scraper"""
    scraper = WillysBrowserScraper(headless=True)
    
    try:
        results = scraper.scrape_willys_offers()
        
        print(f"\n🎯 Scraping Results Summary")
        print("=" * 50)
        
        total_offers = 0
        for pub_id, data in results.items():
            print(f"📚 {data['publication_name']}: {data['offers_count']} offers")
            total_offers += data['offers_count']
        
        print(f"\n📊 Total offers across all publications: {total_offers}")
        
        if total_offers > 0:
            print(f"✅ SUCCESS: Willys browser scraping working!")
            print(f"📋 Ready to integrate into main scraper system")
        else:
            print(f"❌ No offers extracted - may need further investigation")
        
        return results
    
    except Exception as e:
        print(f"❌ Main execution error: {e}")
        return {}

if __name__ == "__main__":
    main()
