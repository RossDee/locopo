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

class UniversalEreklamkladScraper:
    """Universal scraper supporting both individual offers and catalog modes"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.base_url = "https://ereklamblad.se"
        self.api_base = "https://api.ereklamblad.se"
        
        # Cache for weekly scraping
        self.last_scrape_date = None
        self.cached_offers = {}  # Store by publication_id
    
    def detect_publication_type(self, retailer_slug, publication_id):
        """Detect whether a publication uses individual offers or catalog mode"""
        logger.info(f"Detecting publication type for {retailer_slug}/{publication_id}")
        
        try:
            url = f"{self.base_url}/{retailer_slug}?publication={publication_id}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"Failed to load publication page: {response.status_code}")
                return "unknown"
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Analyze app-data structure
            app_data_elements = soup.find_all(id=lambda x: x and 'app-data' in x)
            
            individual_offers_found = False
            catalog_indicators_found = False
            
            for element in app_data_elements:
                try:
                    content = element.get_text().strip()
                    if not content:
                        continue
                    
                    # Parse JSON segments
                    json_segments = self._extract_json_segments(content)
                    
                    for segment in json_segments:
                        try:
                            data = json.loads(segment)
                            
                            # Check for individual offer indicators
                            offer_ids = self._extract_offer_ids_from_json(data)
                            if offer_ids:
                                individual_offers_found = True
                                logger.info(f"Found {len(offer_ids)} individual offers")
                            
                            # Check for catalog indicators
                            if isinstance(data, dict):
                                if 'publication' in data:
                                    pub_data = data['publication']
                                    if isinstance(pub_data, dict):
                                        if 'pageCount' in pub_data and pub_data.get('pageCount', 0) > 1:
                                            catalog_indicators_found = True
                                            logger.info(f"Found catalog with {pub_data['pageCount']} pages")
                                        
                                        if 'images' in pub_data and isinstance(pub_data['images'], list):
                                            catalog_indicators_found = True
                                            logger.info(f"Found catalog images: {len(pub_data['images'])} items")
                            
                        except json.JSONDecodeError:
                            continue
                
                except Exception as e:
                    logger.debug(f"Error analyzing app-data: {e}")
                    continue
            
            if individual_offers_found:
                publication_type = "individual_offers"
            elif catalog_indicators_found:
                publication_type = "catalog"
            else:
                publication_type = "unknown"
            
            logger.info(f"Publication type detected: {publication_type}")
            return publication_type
            
        except Exception as e:
            logger.error(f"Error detecting publication type: {e}")
            return "unknown"
    
    def scrape_offers(self, retailer_slug, publication_id, force_refresh=False):
        """Universal offer scraping supporting both modes"""
        now = datetime.now()
        cache_key = f"{retailer_slug}_{publication_id}"
        
        # Check cache
        if not force_refresh and cache_key in self.cached_offers:
            cache_entry = self.cached_offers[cache_key]
            if cache_entry['timestamp'] and (now - cache_entry['timestamp']).days < 7:
                logger.info(f"Using cached offers for {cache_key}: {len(cache_entry['offers'])} items")
                return cache_entry['offers']
        
        logger.info(f"Starting fresh scrape for {retailer_slug}/{publication_id}")
        
        # Detect publication type
        pub_type = self.detect_publication_type(retailer_slug, publication_id)
        
        offers = []
        
        if pub_type == "individual_offers":
            offers = self._scrape_individual_offers(retailer_slug, publication_id)
        elif pub_type == "catalog":
            offers = self._scrape_catalog_offers(retailer_slug, publication_id)
        else:
            logger.warning(f"Unknown publication type, trying both methods")
            # Try individual offers first
            offers = self._scrape_individual_offers(retailer_slug, publication_id)
            if not offers:
                offers = self._scrape_catalog_offers(retailer_slug, publication_id)
        
        # Cache results
        self.cached_offers[cache_key] = {
            'offers': offers,
            'timestamp': now,
            'type': pub_type
        }
        
        logger.info(f"Scraping complete for {cache_key}: {len(offers)} offers found")
        return offers
    
    def _scrape_individual_offers(self, retailer_slug, publication_id):
        """Scrape individual offers (like ICA Maxi)"""
        logger.info("Using individual offers mode")
        
        offers = []
        
        # Get offer IDs from publication page
        offer_ids = self._extract_offer_ids_from_publication(retailer_slug, publication_id)
        
        if not offer_ids:
            # Try pattern-based discovery with some seed IDs
            logger.info("No IDs found on publication page, trying pattern discovery")
            # You could add known seed IDs for different retailers here
            seed_ids = []
            if retailer_slug.lower() == "ica-maxi-stormarknad":
                seed_ids = ["QKw9mX46Cnk4AU70rkjh3", "InFrprJEuqAJ3Jji23HdH", "uEmpTS_uyXQ5tPdCuWNQv"]
            
            offer_ids = self._discover_offers_by_patterns(retailer_slug, publication_id, seed_ids)
        
        # Extract data for each offer
        for offer_id in offer_ids:
            offer_data = self._extract_individual_offer_data(retailer_slug, publication_id, offer_id)
            if offer_data:
                offers.append(offer_data)
        
        return offers
    
    def _scrape_catalog_offers(self, retailer_slug, publication_id):
        """Scrape catalog-style offers (like Coop)"""
        logger.info("Using catalog mode")
        
        offers = []
        
        try:
            url = f"{self.base_url}/{retailer_slug}?publication={publication_id}"
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
                            
                            # Extract catalog information
                            catalog_info = {
                                'id': pub_data.get('publicId', publication_id),
                                'publication_id': publication_id,
                                'business_id': retailer_slug.lower().replace('-', '_'),
                                'name': pub_data.get('name', f'{retailer_slug} Catalog'),
                                'business_name': retailer_slug.replace('-', ' ').title(),
                                'type': 'catalog',
                                'page_count': pub_data.get('pageCount', 0),
                                'valid_from': self._parse_date(pub_data.get('validFrom')),
                                'valid_until': self._parse_date(pub_data.get('validUntil')),
                                'images': pub_data.get('images', []),
                                'url': url
                            }
                            
                            # For catalogs, we create one "offer" representing the entire catalog
                            # In the future, this could be enhanced to extract individual products from catalog pages
                            offers.append(catalog_info)
                            logger.info(f"Extracted catalog: {catalog_info['name']} ({catalog_info['page_count']} pages)")
                            
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        logger.debug(f"Error processing catalog data: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error scraping catalog: {e}")
        
        return offers
    
    def _extract_json_segments(self, content):
        """Extract valid JSON segments from content"""
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
    
    def _extract_offer_ids_from_json(self, json_data):
        """Extract offer IDs from JSON data"""
        offer_ids = set()
        
        def extract_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.lower() in ['id', 'offerid', 'offer_id'] and isinstance(value, str) and len(value) >= 10:
                        offer_ids.add(value)
                    else:
                        extract_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)
        
        extract_recursive(json_data)
        return offer_ids
    
    def _extract_offer_ids_from_publication(self, retailer_slug, publication_id):
        """Extract offer IDs from publication page"""
        # This would use the same logic as the original ICA Maxi scraper
        # Implementation omitted for brevity - use the existing method
        return []
    
    def _discover_offers_by_patterns(self, retailer_slug, publication_id, seed_ids):
        """Pattern-based offer discovery"""
        # Use existing pattern discovery logic
        return seed_ids  # Simplified for demo
    
    def _extract_individual_offer_data(self, retailer_slug, publication_id, offer_id):
        """Extract data for individual offer"""
        # Use existing individual offer extraction logic
        return None  # Simplified for demo
    
    def _parse_date(self, date_str):
        """Parse date string to datetime object"""
        if not date_str:
            return None
            
        try:
            # Handle ISO format dates
            if 'T' in str(date_str):
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Try other formats
            date_formats = [
                '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', 
                '%d.%m.%Y', '%Y-%m-%dT%H:%M:%S'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(str(date_str), fmt)
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error parsing date '{date_str}': {e}")
            
        return None

# Test the universal scraper
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    scraper = UniversalEreklamkladScraper()
    
    print("🧪 Testing Universal eReklamblad Scraper")
    print("=" * 50)
    
    # Test ICA Maxi (individual offers)
    print("\\n📊 Testing ICA Maxi (Individual Offers Mode)...")
    ica_offers = scraper.scrape_offers("ICA-Maxi-Stormarknad", "5X0fxUgs")
    print(f"   Result: {len(ica_offers)} items")
    
    # Test Coop (catalog mode)  
    print("\\n📖 Testing Coop (Catalog Mode)...")
    coop_offers = scraper.scrape_offers("Coop", "suVwNFKv")
    print(f"   Result: {len(coop_offers)} items")
    
    if coop_offers:
        catalog = coop_offers[0]
        print(f"   📋 Catalog: {catalog.get('name')}")
        print(f"   📄 Pages: {catalog.get('page_count')}")
        print(f"   📅 Valid until: {catalog.get('valid_until')}")
        print(f"   🖼️ Images: {len(catalog.get('images', []))} items")
    
    print("\\n✅ Universal scraper test complete!")
