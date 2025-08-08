#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the enhanced eReklamblad scraper
"""

import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from locopon.scraper import EreklamkladScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_scraper():
    """Test the enhanced scraper functionality"""
    print("🚀 Testing Enhanced eReklamblad Scraper...")
    
    # Initialize scraper
    scraper = EreklamkladScraper()
    
    # Test 1: Discover offers
    print("\n📡 Testing offer discovery...")
    offers = scraper.discover_offers(force_refresh=True)
    print(f"✅ Discovered {len(offers)} offers")
    
    if offers:
        # Test 2: Extract detailed data for first few offers
        print(f"\n📝 Testing data extraction for first 3 offers...")
        
        for i, offer_id in enumerate(offers[:3]):
            print(f"\n🔍 Extracting data for offer {i+1}: {offer_id}")
            offer_data = scraper.extract_offer_data(offer_id)
            
            if offer_data:
                print(f"  ✅ Name: {offer_data.name}")
                print(f"  ✅ Price: {offer_data.price} {offer_data.currency}")
                print(f"  ✅ Business: {offer_data.business_name}")
                if offer_data.description:
                    print(f"  ✅ Description: {offer_data.description[:100]}...")
                if offer_data.image_url:
                    print(f"  ✅ Has image: Yes")
                if offer_data.valid_until:
                    print(f"  ✅ Valid until: {offer_data.valid_until}")
            else:
                print(f"  ❌ Failed to extract data")
    
    # Test 3: Weekly caching
    print(f"\n🗂️ Testing weekly caching...")
    cached_offers = scraper.discover_offers()  # Should use cache
    print(f"✅ Cached offers: {len(cached_offers)} (should be same as discovered)")
    
    print(f"\n🎉 Test completed!")
    print(f"📊 Summary:")
    print(f"  - Total offers found: {len(offers)}")
    print(f"  - Caching working: {'✅' if len(cached_offers) == len(offers) else '❌'}")

if __name__ == "__main__":
    test_scraper()
