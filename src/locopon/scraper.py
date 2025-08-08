#!/usr/bin/env python3  
# -*- coding: utf-8 -*-

import requests
import json
import logging
import time
import random
import string
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class EreklamkladScraper:
    """Enhanced universal scraper supporting multiple retailers and publication types"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
            # Remove Accept-Encoding to let requests handle compression automatically
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Support multiple retailers
        self.retailers = {
            'ica-maxi': {
                'publication_id': '5X0fxUgs',
                'slug': 'ICA-Maxi-Stormarknad',
                'name': 'ICA Maxi',
                'seed_offers': [
                    "QKw9mX46Cnk4AU70rkjh3",  # Brie-, getost
                    "InFrprJEuqAJ3Jji23HdH",  # Chokladkaka  
                    "uEmpTS_uyXQ5tPdCuWNQv",  # Vika Knäckebröd
                    "em9yvCtQ7djrVR83KsdMP",  # Köksredskap
                    "Xehoqb8oZJH4Bf8_K416Q",  # Schampo, balsam, duschcreme
                ]
            },
            'coop': {
                'publication_id': 'suVwNFKv',
                'slug': 'Coop',
                'name': 'Coop',
                'seed_offers': []
            }
        }
        
        self.base_url = "https://ereklamblad.se"
        self.api_base = "https://api.ereklamblad.se"
        
        # Cache for weekly scraping
        self.last_scrape_date = {}  # Per retailer
        self.cached_offers = {}     # Per retailer
    
    def discover_offers(self, force_refresh=False, retailers=None):
        """Discover all offers from supported retailers - only scrape weekly unless forced"""
        now = datetime.now()
        
        # Default to all retailers if none specified
        if retailers is None:
            retailers = list(self.retailers.keys())
        elif isinstance(retailers, str):
            retailers = [retailers]
        
        all_offers = []
        
        for retailer_key in retailers:
            if retailer_key not in self.retailers:
                logger.warning(f"Unknown retailer: {retailer_key}")
                continue
                
            retailer = self.retailers[retailer_key]
            
            # Check if we need to refresh (weekly or forced)
            if not force_refresh and retailer_key in self.last_scrape_date:
                days_since_scrape = (now - self.last_scrape_date[retailer_key]).days
                if days_since_scrape < 7 and retailer_key in self.cached_offers:
                    logger.info(f"Using cached offers for {retailer['name']} ({len(self.cached_offers[retailer_key])} items), last scraped {days_since_scrape} days ago")
                    all_offers.extend(self.cached_offers[retailer_key])
                    continue
            
            logger.info(f"Starting comprehensive offer discovery for {retailer['name']}...")
            
            # Detect publication type and scrape accordingly
            pub_type = self._detect_publication_type(retailer['slug'], retailer['publication_id'])
            retailer_offers = []
            
            if pub_type == "individual_offers":
                retailer_offers = self._scrape_individual_offers(retailer_key)
            elif pub_type == "catalog":
                retailer_offers = self._scrape_catalog_offers(retailer_key)
            else:
                logger.warning(f"Unknown publication type for {retailer['name']}, trying individual offers mode")
                retailer_offers = self._scrape_individual_offers(retailer_key)
            
            # Cache results
            self.cached_offers[retailer_key] = retailer_offers
            self.last_scrape_date[retailer_key] = now
            
            all_offers.extend(retailer_offers)
            logger.info(f"Discovery complete for {retailer['name']}: found {len(retailer_offers)} offers")
        
        logger.info(f"Total discovery complete: found {len(all_offers)} offers from {len(retailers)} retailers")
        return all_offers
    
    def _detect_publication_type(self, retailer_slug, publication_id):
        """Detect whether a publication uses individual offers or catalog mode"""
        try:
            url = f"{self.base_url}/{retailer_slug}?publication={publication_id}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                return "unknown"
            
            soup = BeautifulSoup(response.text, 'html.parser')
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
            
            individual_offers_found = False
            catalog_indicators_found = False
            
            for element in app_data_elements:
                try:
                    content = element.get_text().strip()
                    if not content:
                        continue
                    
                    json_segments = self._extract_json_segments(content)
                    
                    for segment in json_segments:
                        try:
                            data = json.loads(segment)
                            
                            # Check for individual offer indicators
                            offer_ids = self._extract_offers_from_json(data)
                            if offer_ids:
                                individual_offers_found = True
                            
                            # Check for catalog indicators
                            if isinstance(data, dict) and 'publication' in data:
                                pub_data = data['publication']
                                if isinstance(pub_data, dict):
                                    if 'pageCount' in pub_data and pub_data.get('pageCount', 0) > 1:
                                        catalog_indicators_found = True
                                    if 'images' in pub_data and isinstance(pub_data['images'], list) and len(pub_data['images']) > 1:
                                        catalog_indicators_found = True
                        
                        except json.JSONDecodeError:
                            continue
                
                except Exception:
                    continue
            
            if individual_offers_found:
                return "individual_offers"
            elif catalog_indicators_found:
                return "catalog"
            else:
                return "unknown"
                
        except Exception as e:
            logger.debug(f"Error detecting publication type: {e}")
            return "unknown"
    
    def _extract_json_segments(self, content):
        """Extract valid JSON segments from content that may contain multiple JSON objects"""
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
        
        return json_segments
    
    def _scrape_individual_offers(self, retailer_key):
        """Scrape individual offers (like ICA Maxi)"""
        retailer = self.retailers[retailer_key]
        offers = []
        
        # Try multiple approaches to get all offers
        all_offer_ids = set()
        
        # Method 1: Parse main publication page for offer IDs
        offer_ids = self._extract_offers_from_publication_page(retailer['slug'], retailer['publication_id'])
        all_offer_ids.update(offer_ids)
        
        # Method 2: Try to find API endpoints
        api_offers = self._extract_offers_from_api(retailer['publication_id'])
        all_offer_ids.update(api_offers)
        
        # Method 3: Enhanced pattern-based discovery using seeds
        if retailer['seed_offers']:
            pattern_offers = self._discover_offers_by_patterns(retailer['slug'], retailer['publication_id'], retailer['seed_offers'])
            all_offer_ids.update(pattern_offers)
        
        # Extract data for each offer
        for offer_id in all_offer_ids:
            offer_data = self.extract_offer_data(offer_id, retailer['slug'], retailer['publication_id'])
            if offer_data:
                offers.append(offer_data)
        
        return offers
    
    def _scrape_catalog_offers(self, retailer_key):
        """Scrape catalog-style offers (like Coop)"""
        retailer = self.retailers[retailer_key]
        offers = []
        
        try:
            url = f"{self.base_url}/{retailer['slug']}?publication={retailer['publication_id']}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                return offers
            
            soup = BeautifulSoup(response.text, 'html.parser')
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
            
            for element in app_data_elements:
                content = element.get_text().strip()
                if not content:
                    continue
                
                json_segments = self._extract_json_segments(content)
                
                for segment in json_segments:
                    try:
                        data = json.loads(segment)
                        
                        if isinstance(data, dict) and 'publication' in data:
                            pub_data = data['publication']
                            
                            if isinstance(pub_data, dict):
                                from .models import Offer
                                
                                # Create catalog-style offer
                                catalog_offer = Offer(
                                    id=f"catalog_{retailer['publication_id']}",
                                    publication_id=retailer['publication_id'],
                                    business_id=retailer_key,
                                    name=f"{retailer['name']} Catalog - {pub_data.get('name', 'Current Offers')}",
                                    description=f"Complete {retailer['name']} catalog with {pub_data.get('pageCount', 0)} pages of offers",
                                    business_name=retailer['name'],
                                    url=url,
                                    valid_until=self._parse_date(pub_data.get('validUntil')),
                                    # Special fields for catalog
                                    page_count=pub_data.get('pageCount', 0),
                                    catalog_images=pub_data.get('images', [])
                                )
                                
                                offers.append(catalog_offer)
                                logger.info(f"Extracted catalog: {catalog_offer.name}")
                            
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        logger.debug(f"Error processing catalog data: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error scraping catalog: {e}")
        
        return offers
    
    def _extract_offers_from_publication_page(self, retailer_slug, publication_id):
        """Extract offer IDs from the main publication page - enhanced with app-data parsing"""
        logger.info("Extracting offers from publication page...")
        offers = set()
        
        try:
            url = f"{self.base_url}/{retailer_slug}?publication={publication_id}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"Failed to load publication page: {response.status_code}")
                return offers
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Strategy 1: Parse app-data elements (most reliable for modern SPAs)
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
            for element in app_data_elements:
                try:
                    data_content = element.get_text()
                    if data_content:
                        # Try to parse as JSON
                        try:
                            json_data = json.loads(data_content)
                            offers.update(self._extract_offers_from_json(json_data))
                        except json.JSONDecodeError:
                            # Fall back to regex extraction
                            id_patterns = [
                                r'"id"\s*:\s*"([a-zA-Z0-9_-]{10,})"',
                                r'"offerId"\s*:\s*"([a-zA-Z0-9_-]{10,})"',
                                r'"offer_id"\s*:\s*"([a-zA-Z0-9_-]{10,})"'
                            ]
                            for pattern in id_patterns:
                                matches = re.findall(pattern, data_content)
                                offers.update(matches)
                except Exception as e:
                    logger.debug(f"Error parsing app-data element: {e}")
                    continue
            
            # Strategy 2: Look for Next.js data elements
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data:
                try:
                    data = json.loads(next_data.get_text())
                    offers.update(self._extract_offers_from_json(data))
                except Exception as e:
                    logger.debug(f"Error parsing Next.js data: {e}")
            
            # Strategy 3: Enhanced JavaScript variable extraction
            js_content = response.text
            offer_patterns = [
                r'offers?\s*:\s*\[(.*?)\]',  # Array of offers
                r'publication.*?offers?\s*:\s*\[(.*?)\]',
                r'offer["\']?\s*:\s*["\']([a-zA-Z0-9_-]{10,})["\']',
                r'offerId["\']?\s*:\s*["\']([a-zA-Z0-9_-]{10,})["\']',
                r'id["\']?\s*:\s*["\']([a-zA-Z0-9_-]{17})["\']',  # Standard length
                r'/offer/([a-zA-Z0-9_-]{10,})',
                r'&offer=([a-zA-Z0-9_-]{10,})',
                r'window\.__INITIAL_STATE__.*?"offers":\[(.*?)\]'
            ]
            
            for pattern in offer_patterns:
                matches = re.findall(pattern, js_content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    if len(match) >= 10:  # Direct ID match
                        offers.add(match)
                    else:  # Array content - extract IDs
                        id_matches = re.findall(r'["\']([a-zA-Z0-9_-]{10,})["\']', match)
                        offers.update(id_matches)
            
            # Strategy 4: Look in data attributes and links
            for element in soup.find_all(attrs={"data-offer-id": True}):
                offers.add(element.get("data-offer-id"))
                
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'offer=' in href:
                    match = re.search(r'offer=([a-zA-Z0-9_-]+)', href)
                    if match:
                        offers.add(match.group(1))
            
            # Clean up offers - remove invalid/short IDs
            valid_offers = {offer for offer in offers if len(offer) >= 10 and re.match(r'^[a-zA-Z0-9_-]+$', offer)}
            
            logger.info(f"Found {len(valid_offers)} offers from publication page")
            
            return valid_offers
            
        except Exception as e:
            logger.error(f"Error extracting offers from publication page: {e}")
            
        return offers
    
    def _extract_offers_from_json(self, json_data):
        """Recursively extract offer IDs from JSON data structure"""
        offers = set()
        
        def extract_recursive(obj):
            if isinstance(obj, dict):
                # Look for offer-related keys
                for key, value in obj.items():
                    if key.lower() in ['id', 'offerid', 'offer_id', 'offerId'] and isinstance(value, str) and len(value) >= 10:
                        offers.add(value)
                    elif key.lower() in ['offers', 'items', 'data', 'results'] and isinstance(value, list):
                        for item in value:
                            extract_recursive(item)
                    else:
                        extract_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)
        
        extract_recursive(json_data)
        return offers
    
    def _extract_offers_from_api(self, publication_id):
        """Try to find and use API endpoints for offer data"""
        logger.info("Attempting to find API endpoints...")
        offers = set()
        
        # Common API patterns for eReklamblad
        api_endpoints = [
            f"{self.api_base}/publications/{publication_id}/offers",
            f"{self.api_base}/v1/publications/{publication_id}/offers",
            f"{self.api_base}/v2/publications/{publication_id}/offers",
            f"{self.base_url}/api/publications/{publication_id}/offers",
            f"{self.base_url}/api/v1/publications/{publication_id}/offers"
        ]
        
        for endpoint in api_endpoints:
            try:
                logger.debug(f"Trying API endpoint: {endpoint}")
                response = self.session.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Parse different possible JSON structures
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and 'id' in item:
                                    offers.add(item['id'])
                        elif isinstance(data, dict):
                            # Check various common field names
                            for key in ['offers', 'data', 'items', 'results']:
                                if key in data and isinstance(data[key], list):
                                    for item in data[key]:
                                        if isinstance(item, dict) and 'id' in item:
                                            offers.add(item['id'])
                        
                        if offers:
                            logger.info(f"Found {len(offers)} offers from API: {endpoint}")
                            break  # Use first successful API
                            
                    except json.JSONDecodeError:
                        continue
                        
            except Exception as e:
                logger.debug(f"API endpoint {endpoint} failed: {e}")
                continue
        
        return offers
    
    def _discover_offers_by_patterns(self, retailer_slug, publication_id, seed_offers):
        """Enhanced pattern-based discovery using known offers as seeds"""
        if not seed_offers:
            logger.info("No seed offers provided for pattern discovery")
            return set()
        
        logger.info(f"Pattern-based discovery using {len(seed_offers)} seeds...")
        valid_offers = set(seed_offers)
        
        # More sophisticated pattern generation
        for attempt in range(200):  # Increased attempts
            base_id = random.choice(seed_offers)
            
            # Multiple mutation strategies
            strategies = [
                self._mutate_single_char,
                self._mutate_multiple_chars,
                self._mutate_similar_pattern,
                self._generate_variant_id
            ]
            
            strategy = random.choice(strategies)
            new_id = strategy(base_id)
            
            if new_id not in valid_offers and len(new_id) == len(base_id):
                if self._test_offer_exists(new_id, retailer_slug, publication_id):
                    valid_offers.add(new_id)
                    seed_offers.append(new_id)  # Add to seed pool
                    logger.info(f"Found new offer via patterns: {new_id}")
        
        return valid_offers - set(seed_offers)  # Return only new ones
    
    def _mutate_single_char(self, offer_id):
        """Single character mutation"""
        pos = random.randint(0, len(offer_id) - 1)
        new_char = random.choice(string.ascii_letters + string.digits + '_-')
        return offer_id[:pos] + new_char + offer_id[pos+1:]
    
    def _mutate_multiple_chars(self, offer_id):
        """Multiple character mutations"""
        result = list(offer_id)
        num_changes = random.randint(1, min(3, len(offer_id) // 3))
        positions = random.sample(range(len(offer_id)), num_changes)
        
        for pos in positions:
            result[pos] = random.choice(string.ascii_letters + string.digits + '_-')
        
        return ''.join(result)
    
    def _mutate_similar_pattern(self, offer_id):
        """Preserve character type patterns (letter/digit/special)"""
        result = []
        for char in offer_id:
            if char.isalpha():
                result.append(random.choice(string.ascii_letters))
            elif char.isdigit():
                result.append(random.choice(string.digits))
            else:
                result.append(random.choice('_-'))
        return ''.join(result)
    
    def _generate_variant_id(self, offer_id):
        """Generate variant by changing prefix/suffix"""
        mid_point = len(offer_id) // 2
        if random.choice([True, False]):
            # Change prefix
            prefix_len = random.randint(1, mid_point)
            new_prefix = ''.join(random.choices(string.ascii_letters + string.digits, k=prefix_len))
            return new_prefix + offer_id[prefix_len:]
        else:
            # Change suffix
            suffix_len = random.randint(1, mid_point)
            new_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=suffix_len))
            return offer_id[:-suffix_len] + new_suffix

    def _mutate_id(self, offer_id):
        """Legacy method for compatibility"""
        return self._mutate_single_char(offer_id)

    def _test_offer_exists(self, offer_id, retailer_slug=None, publication_id=None):
        """Enhanced offer existence test"""
        try:
            # Use defaults if not provided
            if not retailer_slug:
                retailer_slug = "ICA-Maxi-Stormarknad"
            if not publication_id:
                publication_id = "5X0fxUgs"
            
            # Test multiple URLs
            test_urls = [
                f"{self.base_url}/{retailer_slug}?publication={publication_id}&offer={offer_id}",
                f"{self.base_url}/offer/{offer_id}",
                f"{self.api_base}/offers/{offer_id}"
            ]
            
            for url in test_urls:
                try:
                    response = self.session.get(url, timeout=8)
                    
                    # Check for success indicators
                    if response.status_code == 200:
                        content = response.text.lower()
                        # Look for positive indicators and avoid error indicators
                        positive_signs = [offer_id.lower(), 'offer', 'price', 'product']
                        negative_signs = ['not found', '404', 'error', 'ingen erbjudande']
                        
                        has_positive = any(sign in content for sign in positive_signs)
                        has_negative = any(sign in content for sign in negative_signs)
                        
                        if has_positive and not has_negative:
                            return True
                            
                except:
                    continue
                    
            return False
            
        except Exception as e:
            logger.debug(f"Error testing offer {offer_id}: {e}")
            return False

    def extract_offer_data(self, offer_id, retailer_slug=None, publication_id=None):
        """Extract comprehensive offer data from the website"""
        try:
            from .models import Offer
            
            # Use defaults if not provided (for backward compatibility)
            if not retailer_slug:
                retailer_slug = "ICA-Maxi-Stormarknad"
            if not publication_id:
                publication_id = "5X0fxUgs"
            
            # Primary URL for offer details
            url = f"{self.base_url}/{retailer_slug}?publication={publication_id}&offer={offer_id}"
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                logger.warning(f"Failed to load offer {offer_id}: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            content = response.text
            
            # Extract offer details using multiple strategies
            offer_data = self._parse_offer_from_html(soup, content, offer_id)
            
            if offer_data:
                return Offer(
                    id=offer_id,
                    publication_id=publication_id,
                    business_id=retailer_slug.lower().replace('-', '_'),
                    name=offer_data.get('name', f'Produkt {offer_id[:8]}'),
                    description=offer_data.get('description'),
                    price=offer_data.get('current_price'),
                    original_price=offer_data.get('original_price'),
                    currency=offer_data.get('currency', 'SEK'),
                    business_name=offer_data.get('business_name', retailer_slug.replace('-', ' ').title()),
                    image_url=offer_data.get('image_url'),
                    valid_until=self._parse_date(offer_data.get('valid_until')),
                    url=url
                )
                
        except Exception as e:
            logger.error(f"Error extracting offer data for {offer_id}: {e}")
            
        return None
    
    def _parse_offer_from_html(self, soup, content, offer_id):
        """Parse offer details from HTML content - enhanced with app-data extraction"""
        offer_data = {}
        
        try:
            # Strategy 1: Parse app-data elements (most reliable based on analysis)
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
            for element in app_data_elements:
                try:
                    data_content = element.get_text().strip()
                    if data_content:
                        json_data = json.loads(data_content)
                        
                        # Extract offer data from the structured data
                        extracted_data = self._extract_offer_from_app_data(json_data, offer_id)
                        if extracted_data:
                            offer_data.update(extracted_data)
                            logger.debug(f"Successfully extracted app-data for offer {offer_id}")
                            
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse app-data JSON for {offer_id}: {e}")
                except Exception as e:
                    logger.debug(f"Error processing app-data for {offer_id}: {e}")
            
            # Strategy 2: Look for JSON-LD structured data
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'offers' in data:
                        offer_info = data['offers']
                        if isinstance(offer_info, list):
                            offer_info = offer_info[0]
                        
                        offer_data.update({
                            'current_price': self._extract_price(offer_info.get('price')),
                            'currency': offer_info.get('priceCurrency', 'SEK'),
                            'name': data.get('name'),
                            'description': data.get('description'),
                            'image_url': data.get('image')
                        })
                except:
                    continue
            
            # Strategy 3: Look for meta properties
            meta_props = {
                'og:title': 'name',
                'og:description': 'description',
                'og:image': 'image_url',
                'product:price:amount': 'current_price',
                'product:price:currency': 'currency'
            }
            
            for prop, field in meta_props.items():
                meta_tag = soup.find('meta', property=prop) or soup.find('meta', attrs={'name': prop})
                if meta_tag and meta_tag.get('content'):
                    if field == 'current_price':
                        offer_data[field] = self._extract_price(meta_tag['content'])
                    else:
                        offer_data[field] = meta_tag['content']
            
            # Strategy 4: Look for price patterns in content (fallback)
            if 'current_price' not in offer_data:
                price_patterns = [
                    r'(\d+)[,.](\d+)\s*kr',
                    r'(\d+)\s*kr',
                    r'price["\']?\s*:\s*["\']?(\d+(?:[,.]?\d+)?)',
                    r'pris["\']?\s*:\s*["\']?(\d+(?:[,.]?\d+)?)'
                ]
                
                for pattern in price_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        price_match = matches[0]
                        if isinstance(price_match, tuple):
                            price_str = '.'.join(price_match)
                        else:
                            price_str = price_match
                        
                        try:
                            offer_data['current_price'] = float(price_str.replace(',', '.'))
                            break
                        except:
                            continue
            
            # Strategy 5: Extract product name from page title or headings (fallback)
            if 'name' not in offer_data:
                # Try page title
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
                    # Clean up title (remove site name, etc.)
                    title = re.sub(r'\s*-\s*ICA.*$', '', title)
                    title = re.sub(r'\s*\|\s*eReklamblad.*$', '', title)
                    if title and len(title) > 3:
                        offer_data['name'] = title
                
                # Try headings if title didn't work
                if 'name' not in offer_data:
                    for heading in soup.find_all(['h1', 'h2', 'h3']):
                        text = heading.get_text().strip()
                        if text and len(text) > 3 and len(text) < 100:
                            offer_data['name'] = text
                            break
            
            # Strategy 6: Look for category information
            category_selectors = [
                '.category', '.breadcrumb', '[data-category]',
                '.product-category', '.offer-category'
            ]
            
            for selector in category_selectors:
                elements = soup.select(selector)
                for element in elements:
                    category_text = element.get_text().strip()
                    if category_text and len(category_text) < 50:
                        offer_data['category'] = category_text
                        break
                if 'category' in offer_data:
                    break
            
            # Strategy 7: Look for validity dates
            date_patterns = [
                r'gäller.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'till.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'valid.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ]
            
            for pattern in date_patterns:
                matches = re.search(pattern, content, re.IGNORECASE)
                if matches:
                    offer_data['valid_until'] = matches.group(1)
                    break
            
        except Exception as e:
            logger.debug(f"Error parsing offer HTML for {offer_id}: {e}")
        
        return offer_data
    
    def _extract_offer_from_app_data(self, json_data, offer_id):
        """Extract offer data from app-data JSON structure"""
        offer_data = {}
        
        def search_recursive(obj, path=""):
            if isinstance(obj, dict):
                # Look for offer-specific data
                if 'id' in obj and obj['id'] == offer_id:
                    # Found matching offer, extract all relevant data
                    offer_data.update({
                        'name': obj.get('name') or obj.get('title') or obj.get('productName'),
                        'description': obj.get('description') or obj.get('productDescription'),
                        'current_price': self._extract_price(obj.get('price') or obj.get('currentPrice') or obj.get('salePrice')),
                        'original_price': self._extract_price(obj.get('originalPrice') or obj.get('regularPrice')),
                        'currency': obj.get('currency') or obj.get('priceCurrency', 'SEK'),
                        'image_url': obj.get('image') or obj.get('imageUrl') or obj.get('thumbnail'),
                        'valid_until': obj.get('validUntil') or obj.get('endDate') or obj.get('expiryDate'),
                        'category': obj.get('category') or obj.get('productCategory'),
                        'business_name': obj.get('retailer') or obj.get('store') or obj.get('businessName', 'ICA Maxi')
                    })
                    return True
                
                # Continue searching in nested objects
                for key, value in obj.items():
                    if search_recursive(value, f"{path}.{key}" if path else key):
                        return True
                        
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if search_recursive(item, f"{path}[{i}]" if path else f"[{i}]"):
                        return True
                        
            return False
        
        search_recursive(json_data)
        
        # Clean up extracted data
        cleaned_data = {}
        for key, value in offer_data.items():
            if value is not None and value != "":
                cleaned_data[key] = value
        
        return cleaned_data
    
    def _extract_price(self, price_str):
        """Extract numeric price from string"""
        if not price_str:
            return None
            
        try:
            if isinstance(price_str, (int, float)):
                return float(price_str)
            
            # Clean up price string
            price_str = str(price_str).strip()
            price_str = re.sub(r'[^\d,.]', '', price_str)
            price_str = price_str.replace(',', '.')
            
            if price_str:
                return float(price_str)
                
        except:
            pass
            
        return None
    
    def _parse_date(self, date_str):
        """Parse date string to datetime object"""
        if not date_str:
            return None
            
        try:
            # Try different date formats common in Swedish sites
            date_formats = [
                '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d',
                '%d/%m/%y', '%d-%m-%y', '%y-%m-%d',
                '%d.%m.%Y', '%d.%m.%y'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error parsing date '{date_str}': {e}")
            
        return None
