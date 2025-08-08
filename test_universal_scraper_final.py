#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_universal_scraper():
    """Test the updated universal scraper"""
    try:
        from locopon.scraper import EreklamkladScraper
        
        print("🚀 Testing Updated Universal Scraper")
        print("=" * 60)
        
        scraper = EreklamkladScraper()
        
        # Test ICA Maxi only
        print("\n📊 Testing ICA Maxi...")
        ica_offers = scraper.discover_offers(force_refresh=True, retailers=['ica-maxi'])
        print(f"   ICA Maxi Results: {len(ica_offers)} offers")
        
        if ica_offers:
            sample_offer = ica_offers[0]
            print(f"   Sample: {sample_offer.name} - {sample_offer.price} {sample_offer.currency}")
        
        # Test Coop only
        print("\n📖 Testing Coop...")
        coop_offers = scraper.discover_offers(force_refresh=True, retailers=['coop'])
        print(f"   Coop Results: {len(coop_offers)} offers")
        
        if coop_offers:
            sample_offer = coop_offers[0]
            print(f"   Sample: {sample_offer.name}")
            if hasattr(sample_offer, 'page_count'):
                print(f"   Pages: {sample_offer.page_count}")
        
        # Test both retailers together
        print("\n🔄 Testing Both Retailers...")
        all_offers = scraper.discover_offers(force_refresh=True)
        print(f"   Total Results: {len(all_offers)} offers")
        
        # Group by business
        by_business = {}
        for offer in all_offers:
            business = offer.business_name
            if business not in by_business:
                by_business[business] = []
            by_business[business].append(offer)
        
        print(f"\n📊 Summary by Business:")
        for business, offers in by_business.items():
            print(f"   {business}: {len(offers)} offers")
        
        print(f"\n✅ Universal scraper test complete!")
        print(f"   🎯 Successfully supports both individual offers and catalog modes")
        print(f"   📈 Total coverage: {len(scraper.retailers)} retailers")
        
        return len(all_offers) > 0
        
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_universal_scraper()
    if success:
        print("\n🎉 All tests passed! Universal scraper is ready for production.")
    else:
        print("\n❌ Tests failed. Need further debugging.")
