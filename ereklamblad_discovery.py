#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
from bs4 import BeautifulSoup

class EreklambladseScraper:
    """Complete eReklamblad.se scraper with location selection and retailer discovery"""
    
    def __init__(self, headless=True, debug=False):
        self.headless = headless
        self.debug = debug
        self.driver = None
        
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
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        if not self.debug:
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
            print("🧹 Browser closed")
    
    def select_location(self, location="Stockholm"):
        """Select location on eReklamblad.se"""
        self._setup_driver()
        
        print(f"📍 Selecting location: {location}")
        print("=" * 50)
        
        try:
            # Load the main page
            print("📡 Loading eReklamblad.se...")
            self.driver.get("https://ereklamblad.se/")
            
            # Wait for page to load
            time.sleep(5)
            
            print("🔍 Looking for location selector...")
            
            # Try different possible selectors for location/address input
            location_selectors = [
                'input[placeholder*="address"]',
                'input[placeholder*="location"]', 
                'input[placeholder*="stad"]',
                'input[placeholder*="city"]',
                'input[type="search"]',
                '.location-input',
                '.address-input',
                '#location',
                '#address',
                '[data-testid*="location"]',
                '[data-testid*="address"]',
                'input[name*="location"]',
                'input[name*="address"]'
            ]
            
            location_input = None
            for selector in location_selectors:
                try:
                    location_input = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"✅ Found location input with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not location_input:
                print("⚠️ No location input found with common selectors")
                print("🔍 Searching for all input elements...")
                
                # Find all input elements and check their attributes
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                print(f"📊 Found {len(all_inputs)} input elements")
                
                for i, inp in enumerate(all_inputs):
                    try:
                        input_type = inp.get_attribute("type")
                        input_placeholder = inp.get_attribute("placeholder") or ""
                        input_name = inp.get_attribute("name") or ""
                        input_id = inp.get_attribute("id") or ""
                        input_class = inp.get_attribute("class") or ""
                        
                        print(f"   {i+1}: type={input_type}, placeholder='{input_placeholder}', name='{input_name}', id='{input_id}', class='{input_class}'")
                        
                        # Check if this looks like a location input
                        location_keywords = ['address', 'location', 'stad', 'city', 'place', 'position']
                        if any(keyword in (input_placeholder + input_name + input_id + input_class).lower() 
                               for keyword in location_keywords):
                            location_input = inp
                            print(f"✅ Selected input {i+1} as location input")
                            break
                            
                    except Exception as e:
                        print(f"   {i+1}: Error getting attributes - {e}")
            
            if location_input:
                print(f"📝 Entering location: {location}")
                
                # Clear and enter location
                location_input.clear()
                location_input.send_keys(location)
                
                time.sleep(2)
                
                # Look for dropdown suggestions or submit button
                print("🔍 Looking for location suggestions or submit...")
                
                suggestion_selectors = [
                    '.suggestion',
                    '.dropdown-item',
                    '.autocomplete-item',
                    '[role="option"]',
                    '.location-suggestion',
                    '.address-suggestion'
                ]
                
                suggestions_found = False
                for selector in suggestion_selectors:
                    try:
                        suggestions = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if suggestions:
                            print(f"📋 Found {len(suggestions)} suggestions with selector: {selector}")
                            
                            # Click on first suggestion that contains our location
                            for suggestion in suggestions:
                                suggestion_text = suggestion.text.lower()
                                if location.lower() in suggestion_text:
                                    print(f"✅ Clicking suggestion: {suggestion.text}")
                                    suggestion.click()
                                    suggestions_found = True
                                    break
                            
                            if suggestions_found:
                                break
                    except Exception as e:
                        continue
                
                if not suggestions_found:
                    # Try pressing Enter or looking for submit button
                    print("⏎ Trying to submit location...")
                    try:
                        from selenium.webdriver.common.keys import Keys
                        location_input.send_keys(Keys.RETURN)
                        time.sleep(3)
                    except:
                        pass
                
                # Wait for location to be processed
                time.sleep(5)
                
                print("✅ Location selection completed")
                return True
            
            else:
                print("❌ Could not find location input field")
                
                # Debug: Save page source for analysis
                if self.debug:
                    with open("debug_page_source.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    print("💾 Page source saved to debug_page_source.html")
                
                return False
                
        except Exception as e:
            print(f"❌ Error selecting location: {e}")
            return False
    
    def discover_retailers(self):
        """Discover all available retailers after location selection"""
        print("\n🏪 Discovering available retailers...")
        print("=" * 50)
        
        if not self.driver:
            print("❌ Browser not initialized")
            return []
        
        try:
            # Wait for retailers to load
            time.sleep(5)
            
            retailers = []
            
            # Get page source and parse
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            print(f"📊 Page content: {len(html_content):,} chars")
            
            # Method 1: Look for retailer links in the DOM
            print("🔍 Method 1: Searching for retailer links...")
            
            retailer_selectors = [
                'a[href*="/"]',  # All internal links
                '.retailer',
                '.store',
                '.brand',
                '[data-retailer]',
                '[data-store]',
                '[data-brand]'
            ]
            
            potential_retailers = set()
            
            for selector in retailer_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        href = element.get('href', '')
                        text = element.get_text(strip=True)
                        
                        # Check if this looks like a retailer link
                        if href and href.startswith('/') and len(href) > 1:
                            retailer_name = href.strip('/').split('/')[0]
                            if retailer_name and len(retailer_name) > 2:
                                potential_retailers.add((retailer_name, text, href))
                
                except Exception as e:
                    continue
            
            print(f"📋 Found {len(potential_retailers)} potential retailers")
            
            # Method 2: Look in app-data for structured retailer info
            print("🔍 Method 2: Searching app-data for retailers...")
            
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
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
                        if isinstance(data, dict):
                            # Look for retailer/business data
                            retailers_found = self._extract_retailers_from_json(data)
                            if retailers_found:
                                for retailer in retailers_found:
                                    retailers.append(retailer)
                    except json.JSONDecodeError:
                        continue
            
            # Method 3: Look for Selenium-clickable retailer elements
            print("🔍 Method 3: Searching for clickable retailer elements...")
            
            try:
                clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    'a, button, [role="button"], [data-testid*="retailer"], [data-testid*="store"], [class*="retailer"], [class*="store"]')
                
                print(f"📊 Found {len(clickable_elements)} clickable elements")
                
                for element in clickable_elements:
                    try:
                        text = element.text.strip()
                        href = element.get_attribute('href') or ''
                        data_attrs = {
                            'retailer': element.get_attribute('data-retailer'),
                            'store': element.get_attribute('data-store'),
                            'brand': element.get_attribute('data-brand')
                        }
                        
                        # Check if this looks like a retailer
                        if text and len(text) > 2 and len(text) < 50:
                            # Common Swedish retailers to recognize
                            swedish_retailers = [
                                'ica', 'coop', 'willys', 'hemköp', 'city gross', 
                                'lidl', 'netto', 'tempo', 'maxi', 'kvantum'
                            ]
                            
                            if (any(retailer in text.lower() for retailer in swedish_retailers) or 
                                any(val for val in data_attrs.values() if val) or
                                (href and '/' in href)):
                                
                                retailer_info = {
                                    'name': text,
                                    'url': href,
                                    'attributes': {k: v for k, v in data_attrs.items() if v}
                                }
                                
                                if retailer_info not in retailers:
                                    retailers.append(retailer_info)
                    
                    except Exception:
                        continue
            
            except Exception as e:
                print(f"⚠️ Method 3 error: {e}")
            
            # Clean up and deduplicate results
            unique_retailers = []
            seen_names = set()
            
            for retailer in retailers:
                name = retailer.get('name', '').lower().strip()
                if name and name not in seen_names and len(name) > 2:
                    seen_names.add(name)
                    unique_retailers.append(retailer)
            
            # Also add potential retailers from method 1
            for retailer_name, text, href in potential_retailers:
                if retailer_name.lower() not in seen_names:
                    unique_retailers.append({
                        'name': text or retailer_name,
                        'url': f'https://ereklamblad.se{href}',
                        'slug': retailer_name
                    })
                    seen_names.add(retailer_name.lower())
            
            print(f"✅ Found {len(unique_retailers)} unique retailers")
            return unique_retailers
            
        except Exception as e:
            print(f"❌ Error discovering retailers: {e}")
            return []
    
    def _extract_retailers_from_json(self, data, path=""):
        """Extract retailer information from JSON data"""
        retailers = []
        
        if isinstance(data, dict):
            # Look for retailer-specific keys
            retailer_keys = ['retailers', 'businesses', 'stores', 'brands', 'companies']
            
            for key in retailer_keys:
                if key in data and isinstance(data[key], list):
                    for item in data[key]:
                        if isinstance(item, dict):
                            retailer_info = self._normalize_retailer_data(item)
                            if retailer_info:
                                retailers.append(retailer_info)
            
            # Also check if current dict is a retailer
            if any(key in data for key in ['name', 'title', 'businessName', 'brandName']):
                retailer_info = self._normalize_retailer_data(data)
                if retailer_info:
                    retailers.append(retailer_info)
            
            # Recurse into nested objects (limited depth)
            if len(path.split('.')) < 3:
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        nested_retailers = self._extract_retailers_from_json(value, f"{path}.{key}" if path else key)
                        retailers.extend(nested_retailers)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    nested_retailers = self._extract_retailers_from_json(item, f"{path}[{i}]")
                    retailers.extend(nested_retailers)
        
        return retailers
    
    def _normalize_retailer_data(self, data):
        """Normalize retailer data to standard format"""
        if not isinstance(data, dict):
            return None
        
        name = (data.get('name') or data.get('title') or 
                data.get('businessName') or data.get('brandName') or '').strip()
        
        if not name or len(name) < 2:
            return None
        
        return {
            'name': name,
            'url': data.get('url') or data.get('link') or data.get('href'),
            'description': data.get('description') or data.get('subtitle'),
            'logo': data.get('logo') or data.get('logoUrl') or data.get('image'),
            'slug': data.get('slug') or data.get('id'),
            'raw_data': data
        }
    
    def run_complete_discovery(self, location="Stockholm"):
        """Complete workflow: select location and discover retailers"""
        print("🎯 Complete eReklamblad.se Discovery")
        print("=" * 60)
        
        try:
            # Step 1: Select location
            success = self.select_location(location)
            if not success:
                print("❌ Failed to select location")
                return []
            
            # Step 2: Discover retailers
            retailers = self.discover_retailers()
            
            # Step 3: Display results
            print(f"\n📊 Discovery Results for {location}")
            print("=" * 60)
            
            if retailers:
                print(f"✅ Found {len(retailers)} retailers:")
                
                for i, retailer in enumerate(retailers, 1):
                    name = retailer.get('name', 'Unknown')
                    url = retailer.get('url', 'No URL')
                    slug = retailer.get('slug', 'No slug')
                    
                    print(f"   {i:2d}. {name}")
                    if url and url != 'No URL':
                        print(f"       🔗 URL: {url}")
                    if slug and slug != 'No slug':
                        print(f"       🆔 Slug: {slug}")
                    print()
                
                return retailers
            
            else:
                print("❌ No retailers found")
                print("🔧 This might indicate:")
                print("   • Location selection didn't work properly")
                print("   • Page structure has changed")
                print("   • Need to wait longer for content to load")
                
                return []
        
        except Exception as e:
            print(f"❌ Discovery error: {e}")
            return []
        
        finally:
            self._cleanup_driver()

def main():
    """Test the complete eReklamblad.se discovery"""
    # Create scraper with visible browser for debugging
    scraper = EreklambladseScraper(headless=True, debug=True)
    
    try:
        # Run complete discovery for Sundsvall
        retailers = scraper.run_complete_discovery("Sundsvall")
        
        if retailers:
            print(f"🎉 SUCCESS: Discovered {len(retailers)} retailers in Sundsvall!")
            
            # Save results to file
            output_file = "sundsvall_retailers.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(retailers, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to {output_file}")
        
        else:
            print("❌ No retailers discovered - check implementation")
        
        return retailers
    
    except Exception as e:
        print(f"❌ Main execution error: {e}")
        return []

if __name__ == "__main__":
    main()
